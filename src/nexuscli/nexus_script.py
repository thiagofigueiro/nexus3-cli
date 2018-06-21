def script_dict(script_name, imports, create_statement=None):
    script_ = {
        'type': 'groovy',
        'name': script_name,
        'content': '{imports}\n{create_statement}\n'.format(**locals()),
    }
    return script_, script_name


def script_imports(import_list):
    import_list = import_list or []
    imports = ''
    for import_ in import_list:
        imports += 'import {};\n'.format(import_)
    return imports


def script_common(parameters):
    script_name = 'create_{}'.format(parameters['name'])
    imports = script_imports(parameters.get('__imports', []))
    return script_name, imports


def script_hosted_maven(maven_parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{versionPolicy}, "
                        "{writePolicy}, "
                        "{layoutPolicy});".format(**maven_parameters))

    return script_dict(
        *script_common(maven_parameters), create_statement=create_statement)


def script_proxy_maven(maven_parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{remoteUrl}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{versionPolicy}, "
                        "{layoutPolicy});".format(**maven_parameters))

    return script_dict(
        *script_common(maven_parameters), create_statement=create_statement)


def script_hosted_yum(parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{writePolicy}, "
                        "{depth});".format(**parameters))

    return script_dict(
        *script_common(parameters), create_statement=create_statement)


def script_proxy_yum(parameters):
    return script_proxy(parameters)


def script_hosted(parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation}, "
                        "{writePolicy});".format(**parameters))

    return script_dict(
        *script_common(parameters), create_statement=create_statement)


def script_proxy(parameters):
    create_statement = ("{__method}("
                        "'{name}', "
                        "'{remoteUrl}', "
                        "'{blobStoreName}', "
                        "{strictContentTypeValidation});".format(**parameters))

    return script_dict(
        *script_common(parameters), create_statement=create_statement)


def script_method_name(repo_type, repo_format):
    method_name_tokens = ['script', repo_type]
    if repo_format is not None:
        method_name_tokens.append(repo_format)
    return '_'.join(method_name_tokens)


def script_method_object(repo_type, repo_format):
    return globals()[script_method_name(repo_type, repo_format)]
