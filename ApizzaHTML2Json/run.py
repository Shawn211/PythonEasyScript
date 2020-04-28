import re
from lxml import etree
import json

# 初始化参数
filename = 'OneDrive系统.html'
info_title = 'OneDrive系统API参考文档'
info_description = 'OneDrive系统API接口文档'

openApi = '3.0.0'
info_version = '0.0.1'

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
        description = '\n\n'.join(descriptions)
        parameters = {
            "pathParameters": [],
            "queryParameters": [],
            "bodyParameters": [],
            "responseSchemaParameters": []
        }
        tables = api.xpath('table')
        for table in tables:
            for parameter in table.xpath('tbody/tr'):
                paramIn = None
                if table.xpath('thead/tr/th/span/text()')[0] == '参数名':
                    paramIn = 'responseSchema'
                elif parameter.xpath('td[4]/text()') and 'inParam' in parameter.xpath('td[4]/text()')[0]:
                    paramIn = 'path'
                else:
                    paramIn = re.sub('参数名', '', table.xpath('thead/tr/th/span/text()')[0]).lower()
                if paramIn == 'responseSchema':
                    schema_name_list = parameter.xpath('td[1]/text()')
                    schema_description_list = parameter.xpath('td[2]/text()')
                    schema_type = parameter.xpath('th[1]/text()')[0]
                    formatted_parameter = {'type': schema_type}
                    if schema_name_list:
                        formatted_parameter['name'] = schema_name_list[0]
                    if schema_description_list:
                        formatted_parameter['description'] = schema_description_list[0]
                    parameters[f'{paramIn}Parameters'].append(formatted_parameter)
                else:
                    parameter_name_list = parameter.xpath('td[1]/text()')
                    # parameter_in = re.sub('参数名', '', table.xpath('thead/tr/th/span/text()')[0]).lower()
                    parameter_in = paramIn
                    parameter_required = parameter.xpath('td[3]/text()')[0]
                    parameter_type = parameter.xpath('td[2]/text()')[0]
                    parameter_description_list = parameter.xpath('td[4]/text()')
                    formatted_parameter = {
                        'in': parameter_in,
                        'required': True if '是' in parameter_required else False,
                        'schema': {
                            'type': parameter_type
                        }
                    }
                    if parameter_name_list:
                        formatted_parameter['name'] = parameter_name_list[0]
                    if parameter_description_list:
                        # formatted_parameter['description'] = parameter_description_list[0]
                        formatted_parameter['description'] = re.sub('inParam', '', parameter_description_list[0])
                    parameters[f'{paramIn}Parameters'].append(formatted_parameter)
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
                if 'required' in param and param['required']:
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
        examples = api.xpath('div[@class="highlight"]//code/text()')
        if len(parameters["responseSchemaParameters"]) or examples:
            pathsJson[url][method]['responses'] = {
                "200": {
                    "description": "请求成功",
                    "content": {
                        "application/json": {}
                    }
                }
            }
            if len(parameters["responseSchemaParameters"]):
                properties = {}
                for param in parameters["responseSchemaParameters"]:
                    properties[param['name']] = {}
                    if 'type' in param:
                        properties[param['name']]['type'] = param['type']
                    if 'description' in param:
                        properties[param['name']]['description'] = param['description']
                pathsJson[url][method]['responses']['200']['content']['application/json']['schema'] = {
                    "type": "object",
                    "properties": properties
                }
            if examples:
                pathsJson[url][method]['responses']['200']['content']['application/json']['examples'] = {
                    "请求成功范例": {
                        "value": json.loads(examples[0])
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
