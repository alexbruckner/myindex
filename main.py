import os, sys, re, glob, logging, string

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
        self.vals = {}
        self.id = id
        self.vals["text"] = text

    def add(self, field, value):
        self.vals[field] = value
        return self


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

        for field in indexDoc.doc.vals:

            # add document to data dir
            replace = not Utils.makedirs("%s/#%s" % (indexDoc.dir, field))
            
            # write text to document folder
            with open("data/%s/#%s/text" % (indexDoc.doc.id, field), 'w') as f:
                f.write(indexDoc.doc.vals[field])

            # create words folder in document folder (this will hold the links to the index folders) 
            if not replace: Utils.makedirs("%s/#%s/words" % (indexDoc.dir, field))
            # else traverse through words and remove link in index before indexing again, then do TF. 
            else: 
                Index.removeFromIndex(indexDoc, field)

            # add words to index (ie create a link in word folder to data dir/doc.id)
            Index.addToIndex(indexDoc, field)


    # assume query to be one word for now - TODO
    def search(self, query, field = None, highlight = False):
        directory = Utils.pathify(query.lower())
        linkDir = "%s/index/%s" % (index.dir, directory)
        result = {}

        pattern = "%s/#*/*=>*" % linkDir

        if field:
            pattern = "%s/#%s/*=>*" % (linkDir, field)

        for link in glob.glob(pattern):
            matchStart = link.index("#") + 1
            match = link[ matchStart : link.index("/", matchStart)]
            docMatch = link[link.index("=>") + 2 :]
            if not match in result:
                result[match] = []
            if highlight:
                docMatch = (docMatch, self.snippet(docMatch, match, query))    
            result[match].append(docMatch)
            
        return result

    
    def snippet(self, docId, field, query, size = 7):
        # TODO default snippet size 
        path = "%s/%s/#%s/text"  % (self.data_dir, docId, field)
        with open (path, "r") as f:
            text = f.read()
            return text.replace(query, "%s%s%s" % ("<em class=\"highlight\">", query, "</em>"))

    @staticmethod
    def addToIndex(indexDoc, field):

        count = {}

        words = indexDoc.doc.vals[field]
        aplhanumericOnlyPattern = re.compile('[\W_]+', re.UNICODE)
        alphaNuymOnly = re.sub(aplhanumericOnlyPattern, ' ', words)

        for word in alphaNuymOnly.lower().split():

            count[word] = 1

            directory = Utils.pathify(word)

            linkDir = "%s/index/%s/#%s" % (index.dir, directory, field)

            Utils.makedirs(linkDir)

            link = "%s/%s" % (linkDir, indexDoc.doc.id)
            
            if not os.path.exists(link):
                # symlink document match back to document [index -> data]
                os.symlink(indexDoc.dir, link)
                # symlink document word to index location [data -> index]
                os.symlink(linkDir, "%s/#%s/words/%s" % (indexDoc.dir, field, word))
            else: 
                # increment count by 1 
                count[word] = count[word] + 1

        for entry in count:
            try:
                directory = Utils.pathify(entry.lower())
                linkDir = "%s/index/%s/#%s" % (index.dir, directory, field)
                link = "%s/%s-%s=>%s" % (linkDir, 100000000000000000 - count[entry], count[entry], indexDoc.doc.id)
                os.symlink(indexDoc.doc.id, link)
            except OSError as error: print error, indexDoc.doc.id, link


    @staticmethod
    def removeFromIndex(indexDoc, field):
        wordsDir = "%s/#%s/words" % (indexDoc.dir, field)
        if os.path.exists(wordsDir):
            for word in os.listdir(wordsDir):
                directory = Utils.pathify(word.lower())
                linkDir = "%s/index/%s/#%s" % (index.dir, directory, field)
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


    log.debug("adding test1 document with text: top hat hat and myfield: mY, ,CAt.")
    index.add(Document("test1", "top hat hat").add("myfield", "mY, ,CAt.")) 
    log.debug("adding test2 document with text: top top cat")
    index.add(Document("test2", "top top cat"))

    print "top", index.search("top")
    print "hat", index.search("hat")
    print "cat", index.search("cat")
    print "-", index.search("-")
    print
    print "cat [myfield only]", index.search("cat", field = "myfield")
    print
    print "top [with highlight]", index.search("top", highlight = True)

 
 # TODO text snippets with highlighting
 # TODO filter queries
 # TODO parent-child relationships
 # TODO paging







