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


# github.com/cloudogu/nexus-claim/blob/develop/scripts/create-Repository.groovy
# TODO: package and read from external .groovy file
def script_create_repo():
    script = """
    import groovy.json.JsonSlurper
    import org.sonatype.nexus.blobstore.api.BlobStoreManager
    import org.sonatype.nexus.repository.config.Configuration
    import org.sonatype.nexus.repository.storage.WritePolicy

    class Repository {
      Map<String,Map<String,Object>> properties = new HashMap<String, Object>()
    }

    if (args != "") {
      log.info("Creating repository with args [${args}]")
      def rep = convertJsonFileToRepo(args)
      def output = createRepository(rep)

      return output
    }

    def createRepository(Repository repo) {
      def conf = createConfiguration(repo)

      try {
        repository.createRepository(conf)
      }
      catch (Exception e){
        return e
      }

      return null
    }

    def convertJsonFileToRepo(String jsonData) {
      def inputJson = new JsonSlurper().parseText(jsonData)
      Repository repo = new Repository()
      inputJson.each {
        repo.properties.put(it.key, it.value)
      }

      return repo
    }

    def createConfiguration(Repository repo){
      def name = getName(repo)
      def recipeName = getRecipeName(repo)
      def online = getOnline(repo)
      def attributes = repo.properties.get("attributes")

      Configuration conf = new Configuration(
        repositoryName: name,
        recipeName: recipeName,
        online: online,
        attributes: attributes
      )

      return conf
    }

    def getName(Repository repo){
      String name = repo.getProperties().get("name")
      return name
    }

    def getRecipeName(Repository repo){
      String recipeName = repo.getProperties().get("recipeName")
      return recipeName
    }

    def getOnline(Repository repo){
      String online = repo.getProperties().get("online")
      return online
    }
    """
    return script
