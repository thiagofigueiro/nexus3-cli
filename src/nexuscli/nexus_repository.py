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
