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


class Document(object):
    def __init__(self, id, text = None):
        self.vals = {}
        self.id = id
        if text:
            self.vals["text"] = text

    def add(self, field, value):
        self.vals[field] = value
        return self

    def get(self, field):
        return self.vals[field]


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
    def search(self, query, field = None, highlight = False, size = 300, paging = -1, start = 0, full = False):
        directory = Utils.pathify(query.lower())
        linkDir = "%s/index/%s" % (index.dir, directory)
        result = {}

        pattern = "%s/#*/*=>*" % linkDir

        if field:
            pattern = "%s/#%s/*=>*" % (linkDir, field)

        for i, link in enumerate(glob.glob(pattern)):
            if paging == -1 or (i >= start and i < start + paging):
                matchStart = link.index("#") + 1
                match = link[ matchStart : link.index("/", matchStart)]
                docMatch = link[link.index("=>") + 2 :]
                docId = docMatch
                if not match in result:
                    result[match] = []
                if highlight:
                    docMatch = (docMatch, self.snippet(docMatch, match, query, size))    
                
                if full:
                    result[match].append(self.load(docId, docMatch))
                else: 
                    result[match].append(docMatch)

        return result


    def load(self, docId, docMatch):
        doc = Document(docId)
        self.loadIntoDoc(doc)
        doc.match = docMatch[1]
        return doc

    def loadIntoDoc(self, doc):

        dir = "%s/%s/#*/text" % (self.data_dir, doc.id)

        for text in glob.glob(dir):
            index = text.index("#")
            field = text[index + 1 : text.index("/", index)]
            with open(text, 'r') as f:
                doc.vals[field] = f.read()
        

    
    def snippet(self, docId, field, query, size):
        # TODO default snippet size 
        path = "%s/%s/#%s/text"  % (self.data_dir, docId, field)
        with open (path, "r") as f:
            text = f.read()
            text = re.sub('<[^<]+?>', ' ', text)
            if size != -1:
                index = max(0, re.search(query, text, re.IGNORECASE).span()[0])
                text = "...%s..." % text[index : min(size, len(text))] # TODO check bounds ...
            return re.sub("(?i)(%s)" % query, r'<em class="hightlight">\1</em>', text)

    @staticmethod
    def addToIndex(indexDoc, field):

        count = {}

        words = indexDoc.doc.vals[field]

        # strip html tags
        words = re.sub('<[^<]+?>', ' ', words)

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
    print "top [with highlight, size 10]", index.search("top", highlight = True, size = 10)
    print
    print "cat [with highlight, size = -1]", index.search("cat", highlight = True, size = -1)
    print
    print "cat [paging = 1]", index.search("cat", paging = 1)
    print
    print "cat [paging = 1, start = 1]", index.search("cat", paging = 1, start = 1)
    print
 
    log.debug("adding test3 html document with text: <p>this is a paragraph</p><p class=\"class\">class: This is \nanother paragraph</p> anbd type: entry.")
    index.add(Document("test3", "<p>this is a paragraph</p><p class=\"class\">class: This is \nanother paragraph</p>").add("type", "entry")) 
 
    print
    print "class [with highlight]", index.search("class", highlight = True)

    print
    print "class [full][text][0].id =", index.search("class", full = True, highlight = True)["text"][0].id
    print
    print "class [full][text][0].match =", index.search("class", full = True, highlight = True)["text"][0].match
    print
    print "class [full][text][0].get('text') =", index.search("class", full = True, highlight = True)["text"][0].get('text')
    print
    print "class [full][text][0].get('type') =", index.search("class", full = True, highlight = True)["text"][0].get('type')


 # TODO filter queries
 # TODO add local files (encode file path as id)
 # TODO exact phrases
 # TODO multipe search words
 # TODO parent-child relationships





