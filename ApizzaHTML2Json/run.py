import re
from lxml import etree
import json

# 初始化参数
filename = 'OneDrive系统.html'
openApi = '3.0.0'
info_title = 'OneDrive系统API参考文档'
info_version = '0.0.1'
info_description = 'OneDrive系统API接口文档'

pathsJson = {}

parser = etree.HTMLParser(encoding="utf-8")
html = etree.parse(filename, parser=parser)
elements = html.xpath('//div[@class="block-doc-one"]/*')[0: -2]
all_api_dict = {}
tagName = None
for element in elements:
    if element.xpath('.')[0].tag == 'h1':
        tagName = element.text
    elif tagName in all_api_dict:
        all_api_dict[tagName].append(element)
    else:
        all_api_dict[tagName] = [element]

for tagName in all_api_dict:
    all_api = all_api_dict[tagName]
    for api in all_api:
        url = re.search(r'请求地址：(.*?)\s+', api.xpath('p[3]/text()')[0]).group(1)
        pathsJson[url] = pathsJson[url] if url in pathsJson else {}
        method = re.search(r'请求方式：(.*)$', api.xpath('p[2]/text()')[0]).group(1).lower()
        if not method:
            break
        descriptions = [re.sub(r'\n\s*', '', p.text) if p.text else '' for p in
                        api.xpath('div[@class="detail-info"]//p')]
        description = '\n'.join(descriptions)
        parameters = {
            "pathParameters": [],
            "queryParameters": [],
            "bodyParameters": []
        }
        tables = api.xpath('table')
        for table in tables:
            for parameter in table.xpath('tbody/tr'):
                paramIn = re.sub('参数名', '', table.xpath('thead/tr/th/span/text()')[0]).lower() \
                    if 'inParam' not in parameter.xpath('td[4]/text()')[0] else 'path'
                parameters[f'{paramIn}Parameters'].append({
                    "name": parameter.xpath('td[1]/text()')[0],
                    # "in": re.sub('参数名', '', table.xpath('thead/tr/th/span/text()')[0]).lower(),
                    "in": paramIn,
                    "required": True if '是' in parameter.xpath('td[3]/text()')[0] else False,
                    "schema": {
                        "type": parameter.xpath('td[2]/text()')[0]
                    },
                    # "description": parameter.xpath('td[4]/text()')[0]
                    "description": re.sub('inParam', '', parameter.xpath('td[4]/text()')[0])
                })
        if 'parameters' not in pathsJson[url] and len(parameters['pathParameters']):
            pathsJson[url] = {
                "parameters": parameters['pathParameters']
            }
        pathsJson[url][method] = {
            "summary": api.xpath('h3[1]/text()')[0],
            "tags": [tagName],
            "description": description,
            "responses": {}
        }
        if len(parameters["queryParameters"]):
            pathsJson[url][method]['parameters'] = parameters['queryParameters']
        if len(parameters["bodyParameters"]):
            properties = {}
            required = []
            for param in parameters["bodyParameters"]:
                properties[param['name']] = {
                    "type": param['schema']['type'],
                    "description": param['description']
                }
                if param['required']:
                    required.append(param['name'])
            pathsJson[url][method]['requestBody'] = {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": properties
                        }
                    }
                }
            }
            if required:
                pathsJson[url][method]['requestBody']['content']['application/json']['schema']['required'] = required
        code = api.xpath('div[@class="highlight"]//code/text()')
        if code:
            pathsJson[url][method]['responses'] = {
                "200": {
                    "description": "请求成功",
                    "content": {
                        "application/json": {
                            "examples": {
                                "请求成功范例": {
                                    "value": json.loads(code[0])
                                }
                            }
                        }
                    }
                }
            }

apiJson = {
    "openapi": openApi,
    "info": {
        "title": info_title,
        "version": info_version,
        "description": info_description
    },
    "paths": pathsJson
}

with open('apiJson.json', 'w+', encoding='utf-8') as f:
    f.write(json.dumps(apiJson, ensure_ascii=False))
