import os, sys, re, glob, logging

log = logging.getLogger('myindex')

class Utils:
    
    @staticmethod
    def pathify(word, char = '/'):        
        return char.join([c for c in word])

    @staticmethod
    def makedirs(directory):
        ok = False
        if not os.path.exists(directory):
                os.makedirs(directory)
                ok = True
        return ok

    @staticmethod
    def purge(dir, pattern):
        for f in os.listdir(dir):
            if re.search(pattern, f):
                os.remove(os.path.join(dir, f))


class Document:
    def __init__(self, id, text):
        self.id = id
        self.text = text

class IndexDocument():
    def __init__(self, index, doc):
        self.index = index
        self.doc = doc
        self.dir = os.path.join(index.data_dir, self.doc.id)

class Index:
    def __init__(self):
        self.dir = os.getcwd()
        self.data_dir = os.path.join(self.dir, "data")
        self.index_dir = os.path.join(self.dir, "index")
        # create data dir

        Utils.makedirs(self.data_dir)

        # create index dir
        Utils.makedirs(self.index_dir)


    def add(self, doc):

        indexDoc = IndexDocument(self, doc)

        # add document to data dir
        replace = not Utils.makedirs(indexDoc.dir)

        # write text to document folder
        with open("data/%s/text" % indexDoc.doc.id, 'w') as f:
            f.write(indexDoc.doc.text)

        # the path to the document
        # docPath = "%s/data/%s" % (self.dir, indexDoc.doc.id)

        # create words folder in document folder (this will hold the links to the index folders) 
        if not replace: Utils.makedirs(indexDoc.dir +  "/words")
        # else traverse through words and remove link in index before indexing again, then do TF. 
        else: 
            Index.removeFromIndex(indexDoc)

        # add words to index (ie create a link in word folder to data dir/doc.id)
        Index.addToIndex(indexDoc)


    # assume query to be one word for now
    def search(self, query):
        directory = Utils.pathify(query)
        linkDir = "index/%s" % directory
        result = []
        for link in glob.glob(linkDir + "/*=>*"):
            result.append(link[link.index("=>") + 2 :])
        return result

    @staticmethod
    def addToIndex(indexDoc):

        count = {}

        for word in indexDoc.doc.text.split():

            count[word] = 1

            directory = Utils.pathify(word)
            Utils.makedirs("index/" + directory)

            linkDir = "%s/index/%s" % (index.dir, directory)
            link = "%s/%s" % (linkDir, indexDoc.doc.id)
            
            if not os.path.exists(link):
                # symlink document match back to document [index -> data]
                os.symlink(indexDoc.dir, link)
                # symlink document word to index location [data -> index]
                os.symlink(linkDir, indexDoc.dir + "/words/" + word)
            else: 
                # TODO increment count by 1 
                count[word] = count[word] + 1

        for entry in count:
            try:
                directory = Utils.pathify(entry)
                linkDir = "%s/index/%s" % (index.dir, directory)
                link = "%s/%s-%s=>%s" % (linkDir, 100000000000000000 - count[entry], count[entry], indexDoc.doc.id)
                os.symlink(indexDoc.doc.id, link)
            except OSError as error: print error, indexDoc.doc.id, link


    @staticmethod
    def removeFromIndex(indexDoc):
        wordsDir = indexDoc.dir + "/words"
        if os.path.exists(wordsDir):
            for word in os.listdir(wordsDir):
                directory = Utils.pathify(word)
                linkDir = "index/%s" % directory
                link = "%s/%s" % (linkDir, indexDoc.doc.id)
                
                # remove link
                os.remove(link)

                # remove count
                Utils.purge(linkDir, "^.*.=>" + indexDoc.doc.id + "$")

                # remove word
                os.remove("%s/%s" % (wordsDir, word))
    



# simple test
if __name__ == '__main__':

    index = Index()
    print "dir is %s" % index.dir


    # TODO move LOGGING into config
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=FORMAT)
    log.setLevel("DEBUG")


    log.debug("adding test1 document with text: top hat hat")
    index.add(Document("test1", "top hat hat")) # TODO upper case 
    log.debug("adding test2 document with text: top top cat")
    index.add(Document("test2", "top top cat"))

    print "top", index.search("top")
    print "hat", index.search("hat")
    print "cat", index.search("cat")
    print "-", index.search("-")
 