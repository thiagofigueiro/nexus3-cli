import groovy.json.JsonBuilder

Boolean exists = repository.repositoryManager.get(args) as Boolean

if (!exists)
    return null

repo_config = repository.repositoryManager.get(args).configuration

def repositoryConfiguration = new JsonBuilder()
repositoryConfiguration repo_config

repositoryConfiguration  {
    repositoryName repo_config.repositoryName
    recipeName repo_config.recipeName
    attributes repo_config.attributes
}

return repositoryConfiguration.toPrettyString()
