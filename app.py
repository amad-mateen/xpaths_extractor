from flask import Flask, render_template, request, jsonify
import requests
from lxml import html, etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException
import time
import os

app = Flask(__name__)

def extract_ids_and_xpaths(page_content):
    parser = html.HTMLParser(encoding='utf-8')
    tree = html.fromstring(page_content, parser=parser)
    elements = tree.xpath('//*')
    results = []
    for el in elements:
        el_id = el.get('id')
        class_name = el.get('class')
        tag_name = el.tag
        # CSS selector
        selector = tag_name
        if el_id:
            selector += f"#{el_id}"
        if class_name:
            selector += ''.join(f".{c}" for c in class_name.split())
        # Attribute selectors (first attribute except id/class)
        attr_selector = ''
        attr_string = ''
        name_attr = el.get('name') if 'name' in el.attrib else ''
        style_attr = el.get('style') if 'style' in el.attrib else ''
        title_attr = el.get('title') if 'title' in el.attrib else ''
        for k, v in el.attrib.items():
            if k not in ('id', 'class') and v:
                if not attr_selector:
                    attr_selector = f'[{k}="{v}"]'
                attr_string += f'{k}="{v}" '
        attr_string = attr_string.strip()
        # Element value/content
        value = el.get('value') if 'value' in el.attrib else ''
        text_content = el.text_content().strip() if hasattr(el, 'text_content') else ''
        # Prefer value for input/button, else text content
        display_value = value or text_content
        # Element type/category
        element_type = ''
        if tag_name == 'a':
            element_type = 'link'
        elif tag_name == 'input':
            input_type = el.get('type', '').lower()
            if input_type == 'checkbox':
                element_type = 'checkbox'
            elif input_type == 'radio':
                element_type = 'radio button'
            elif input_type in ['submit', 'button', 'reset']:
                element_type = 'button'
            elif input_type == 'password':
                element_type = 'password box'
            elif input_type == 'file':
                element_type = 'file upload'
            elif input_type == 'email':
                element_type = 'email box'
            elif input_type == 'number':
                element_type = 'number box'
            elif input_type == 'search':
                element_type = 'search box'
            elif input_type == 'text' or not input_type:
                element_type = 'text box'
            else:
                element_type = input_type
        elif tag_name == 'button':
            element_type = 'button'
        elif tag_name == 'select':
            element_type = 'drop down'
        elif tag_name == 'textarea':
            element_type = 'text area'
        else:
            element_type = tag_name
        try:
            xpath = tree.getroottree().getpath(el)
        except Exception:
            xpath = ''
        results.append({
            'id': el_id,
            'class': class_name,
            'tag': tag_name,
            'name': name_attr,
            'style': style_attr,
            'title': title_attr,
            'css_selector': selector,
            'attr_selector': attr_selector,
            'attr_string': attr_string,
            'display_value': display_value,
            'element_type': element_type,
            'xpath': xpath
        })
    return results

def extract_ids_and_xpaths_selenium(url, skip_ssl=False):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
    if skip_ssl:
        chrome_options.add_argument('--ignore-certificate-errors')
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        return [{'error': f'WebDriver error: {str(e)}'}]
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'textarea.gLFyf[name="q"]'))
        )
    except Exception:
        pass
    time.sleep(2)  
    debug_info = []
    try:
        search_box = driver.find_element(By.CSS_SELECTOR, 'textarea.gLFyf[name="q"]')
        debug_info.append({
            'id': search_box.get_attribute('id'),
            'class': search_box.get_attribute('class'),
            'name': search_box.get_attribute('name'),
            'tag': search_box.tag_name,
            'outerHTML': driver.execute_script('return arguments[0].outerHTML;', search_box)
        })
    except Exception as e:
        debug_info.append({'error': f'Could not find search box: {str(e)}'})
    # Extract all elements and their attributes
    elements = driver.find_elements(By.XPATH, '//*')
    results = []
    for el in elements:
        try:
            el_id = el.get_attribute('id')
            class_name = el.get_attribute('class')
            tag_name = el.tag_name
            name_attr = el.get_attribute('name')
            style_attr = el.get_attribute('style')
            title_attr = el.get_attribute('title')
            jsname_attr = driver.execute_script('return arguments[0].getAttribute("jsname") || arguments[0].attributes["jsname"]?.value || "";', el)
            selector = tag_name
            if el_id:
                selector += f"#{el_id}"
            if class_name:
                selector += ''.join(f".{c}" for c in class_name.split())
            attr_selector = ''
            attr_string = ''
            aria_attrs = {}
            data_attrs = {}
            attrs = driver.execute_script('var items = {}; for (var i = 0; i < arguments[0].attributes.length; ++i) { items[arguments[0].attributes[i].name] = arguments[0].attributes[i].value }; return items;', el)
            for k, v in attrs.items():
                if k.startswith('aria-'):
                    aria_attrs[k] = v
                elif k.startswith('data-'):
                    data_attrs[k] = v
                elif k not in ('id', 'class', 'name', 'jsname') and v:
                    if not attr_selector:
                        attr_selector = f'[{k}="{v}"]'
                    attr_string += f'{k}="{v}" '
            attr_string = attr_string.strip()
            # Element value/content
            value = el.get_attribute('value')
            text_content = el.text.strip() if hasattr(el, 'text') else ''
            display_value = value or text_content
            # Element type/category
            element_type = ''
            if tag_name == 'a':
                element_type = 'link'
            elif tag_name == 'input':
                input_type = (attrs.get('type') or '').lower()
                if input_type == 'checkbox':
                    element_type = 'checkbox'
                elif input_type == 'radio':
                    element_type = 'radio button'
                elif input_type in ['submit', 'button', 'reset']:
                    element_type = 'button'
                elif input_type == 'password':
                    element_type = 'password box'
                elif input_type == 'file':
                    element_type = 'file upload'
                elif input_type == 'email':
                    element_type = 'email box'
                elif input_type == 'number':
                    element_type = 'number box'
                elif input_type == 'search':
                    element_type = 'search box'
                elif input_type == 'text' or not input_type:
                    element_type = 'text box'
                else:
                    element_type = input_type
            elif tag_name == 'button':
                element_type = 'button'
            elif tag_name == 'select':
                element_type = 'drop down'
            elif tag_name == 'textarea':
                element_type = 'text area'
            else:
                element_type = tag_name
            xpath = driver.execute_script('function absoluteXPath(element) { var comp = []; while (element && element.nodeType === 1) { var sib = element.previousSibling, pos = 1; while (sib) { if (sib.nodeType === 1 && sib.nodeName === element.nodeName) pos += 1; sib = sib.previousSibling; } comp.unshift(element.nodeName.toLowerCase() + "[" + pos + "]"); element = element.parentNode; } return "/" + comp.join("/"); } return absoluteXPath(arguments[0]);', el)
            results.append({
                'id': el_id,
                'class': class_name,
                'name': name_attr,
                'style': style_attr,
                'title': title_attr,
                'jsname': jsname_attr,
                'tag': tag_name,
                'css_selector': selector,
                'attr_selector': attr_selector,
                'attr_string': attr_string,
                'aria_attrs': aria_attrs,
                'data_attrs': data_attrs,
                'display_value': display_value,
                'element_type': element_type,
                'xpath': xpath
            })
        except Exception as e:
            results.append({'error': str(e)})
    driver.quit()
    # If the search box was found, add its debug info at the start
    if debug_info:
        results.insert(0, {'debug_search_box': debug_info})
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        skip_ssl = request.form.get('skip_ssl') == 'on'
        only_named_ids = request.form.get('only_named_ids') == 'on'
        mode = request.form.get('mode', 'dynamic')
        try:
            if mode == 'dynamic':
                results = extract_ids_and_xpaths_selenium(url, skip_ssl=skip_ssl)
            else:
                resp = requests.get(url, timeout=10, verify=not skip_ssl)
                resp.raise_for_status()
                results = extract_ids_and_xpaths(resp.content)
            if only_named_ids:
                results = [r for r in results if r.get('id') and r.get('id').strip()]
            return render_template('index.html', results=results, url=url, skip_ssl=skip_ssl, only_named_ids=only_named_ids, mode=mode)
        except Exception as e:
            return render_template('index.html', error=str(e), url=url, skip_ssl=skip_ssl, only_named_ids=only_named_ids, mode=mode)
    return render_template('index.html', mode='dynamic')

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.get_json()
    url = data.get('url')
    skip_ssl = data.get('skip_ssl', False)
    try:
        resp = requests.get(url, timeout=10, verify=not skip_ssl)
        resp.raise_for_status()
        results = extract_ids_and_xpaths(resp.content)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
