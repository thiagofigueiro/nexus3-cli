import groovy.json.JsonSlurper
import org.sonatype.nexus.repository.config.Configuration
import org.sonatype.nexus.repository.manager.RepositoryManager


class Repository {
    Map<String,Map<String,Object>> properties = new HashMap<String, Object>()
}

if (args != "") {
    log.info("Creating repository with args [${args}]")
    def rep = convertJsonFileToRepo(args)
    log.debug("Got repo [${rep}]")
    def output = createRepository(rep)

    return output
}

def createRepository(Repository repo) {
    def conf = createConfiguration(repo)

    try {
        repository.createRepository(conf)
    }
    catch (Exception e) {
        return e
    }

    return null
}

def convertJsonFileToRepo(String jsonData) {
    def inputJson = new JsonSlurper().parseText(jsonData)
    log.debug("Creating repository object for [${inputJson}]")
    Repository repo = new Repository()
    inputJson.each {
        repo.properties.put(it.key, it.value)
    }

    log.debug("Created repository object [${repo}]")
    return repo
}

//def repositoryManager = container.lookup(RepositoryManager.class.getName())

def createConfiguration(Repository repo) {
    repositoryManager = container.lookup(RepositoryManager.class.getName())
    Configuration conf = repositoryManager.newConfiguration()

    conf.with {
      repositoryName = getName(repo)
      recipeName = getRecipeName(repo)
      online = getOnline(repo)
      attributes = repo.properties.get("attributes") as Map
    }

    // https://github.com/thiagofigueiro/nexus3-cli/issues/77
    try {
        policy_name = conf.attributes.cleanup.policyName
        log.info("policy name is ${policy_name.getClass()}")
        if (policy_name.getClass() == java.util.ArrayList) {
            Set set = new HashSet(policy_name)
            conf.attributes.cleanup.policyName = set
            log.info("Converted to ${set.getClass()}")
        }
    }
    catch (java.lang.NullPointerException e) {
        log.info("No cleanup policy provided; that's ok.")
    }

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
