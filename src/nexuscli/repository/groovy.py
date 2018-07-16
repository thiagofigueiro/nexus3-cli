# Relevant javadocs
# LayoutPolicy, VersionPolicy
# http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/plugins/nexus-repository-maven/3.12.1-01/nexus-repository-maven-3.12.1-01-javadoc.jar
# WritePolicy
# http://search.maven.org/remotecontent?filepath=org/sonatype/nexus/nexus-repository/3.0.2-02/nexus-repository-3.0.2-02-javadoc.jar

POLICY_IMPORTS = {
    'layout': ['org.sonatype.nexus.repository.maven.LayoutPolicy'],
    'version': ['org.sonatype.nexus.repository.maven.VersionPolicy'],
    'write': ['org.sonatype.nexus.repository.storage.WritePolicy'],
}
POLICIES = {
    'layout': {
        'permissive': 'LayoutPolicy.PERMISSIVE',
        'strict': 'LayoutPolicy.STRICT',
    },
    'version': {
        'release': 'VersionPolicy.RELEASE',
        'snapshot': 'VersionPolicy.SNAPSHOT',
        'mixed': 'VersionPolicy.MIXED',
    },
    'write': {
        'allow': 'WritePolicy.ALLOW',
        'allow_once': 'WritePolicy.ALLOW_ONCE',
        'deny': 'WritePolicy.DENY',
    },
}


def recipe_to_groovy_name(recipe_name):
    if recipe_name == 'pypi':
        return 'PyPi'

    return recipe_name.title()


def _method_name_create(repo_format, repo_type):
    """
    Returns the groovy method name as per
    org.sonatype.nexus.repository.Repository. The methods use this
    format: createFormatType. Format is the recipe and Type is Group, Hosted
    or Proxy.
    """
    groovy_name = 'repository.create{}{}'.format(
        recipe_to_groovy_name(repo_format), repo_type.title())
    return groovy_name


# def method_name(action, repo_type, **kwargs):
#     if action == 'create':
#         return _method_name_create(kwargs['format'], repo_type)
#
#     raise ValueError('action={} unknown'.format(action))


def script_create_repository(repo_type, **kwargs):
    # groovy_method = _method_name_create(kwargs['format'], repo_type)
    raise NotImplementedError
