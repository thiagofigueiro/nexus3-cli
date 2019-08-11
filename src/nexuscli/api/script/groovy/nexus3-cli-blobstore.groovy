import groovy.json.JsonBuilder
import groovy.json.JsonSlurper
import org.sonatype.nexus.blobstore.api.BlobStoreManager

blobStoreManager = blobStore.blobStoreManager
parsed_args = new JsonSlurper().parseText(args)


parsed_args.each {
    log.debug("Received arguments: <${it.key}=${it.value}> (${it.value.getClass()})")
}


switch(parsed_args._action) {
    case "list":
        log.debug("list")
        List<String> stores = blobStoreManager.browse()*.blobStoreConfiguration*.name
        return stores;
        break;
    case "get":
        log.debug("get")
        getBlobStore(parsed_args.name)
        break;
    case "create":
        log.debug("create")
        if (parsed_args.file != null) {
            createFileBlobStore(parsed_args.name, parsed_args.path)
        } else if (parsed_args.s3 != null) {
            createS3BlobStore(parsed_args.name, parsed_args.s3)
        } else {
            throw new Exception("blobstore type must be one of: file, s3")
        }
        break;
    case "delete":
        log.debug("delete")
        deleteBlobStore(parsed_args.name)
        break;
    default:
        throw new Exception(
            "action must be one of: list, create, delete; received=${parsed_args._action}")
}


def String getBlobStore(name) {
    existingBlobStore = blobStoreManager.get(name)
    log.error("existingBlobStore: ${existingBlobStore}")

    if (existingBlobStore == null) {
        throw new Exception("blobstore not found: ${name}")
    } else {
        config = existingBlobStore.blobStoreConfiguration.attributes
        return new JsonBuilder(config).toPrettyString()
    }
}


def createFileBlobStore(name, path) {
    existingBlobStore = blobStoreManager.get(name)

    if (existingBlobStore == null) {
        log.debug("Creating blobstore name=${name} path=${path}")
        blobStore.createFileBlobStore(name, path)
        existingBlobStore = blobStore.getBlobStoreManager().get(name)
    }
}


def deleteBlobStore(name) {
    existingBlobStore = blobStoreManager.get(name)

    if (existingBlobStore != null) {
        log.debug("Deleting blobstore name=${name}")
        blobStore.getBlobStoreManager().delete(parsed_args.name)
    }
}
