import os, sys, re

class Utils:
    @staticmethod
    def after_each_character_insert(word, char):        
        path = list()
        for (i, c) in enumerate(word):
            path.append(c)
            if i >= 0 and i < len(word) - 1:
                path.append(char)

        return ''.join(path)


    @staticmethod
    def makedirs(root, directory):
        directory = root + "/" + directory
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


class Index:
    def __init__(self, dir = os.getcwd()):
        self.dir = dir

    def add(self, doc):

        # add document to data dir
        replace = not Utils.makedirs("data", doc.id)

        # write text to document folder
        with open("data/%s/text" % doc.id, 'w') as f:
            f.write(doc.text)

        # the path to the document
        docPath = "%s/data/%s" % (self.dir, doc.id)

        # create words folder in document folder (this will hold the links to the index folders) 
        if not replace: Utils.makedirs(docPath, "words")
        # else traverse through words and remove link in index before indexing again, then do TF. 
        else: 
            Index.removeFromIndex(docPath, doc.id)

        # add words to index (ie create a link in word folder to data dir/doc.id)
        Index.addToIndex(self.dir, doc, docPath)

    @staticmethod
    def addToIndex(root, doc, docPath):

        count = {}

        for word in doc.text.split():

            count[word] = 1

            directory = Utils.after_each_character_insert(word, '/')
            Utils.makedirs("index", directory)

            linkDir = "index/%s" % directory
            link = "%s/%s" % (linkDir, doc.id)
            
            if not os.path.exists(link):
                # symlink document match back to document [index -> data]
                os.symlink(docPath, link)
                # symlink document word to index location [data -> index]
                os.symlink("%s/%s" % (root, linkDir), docPath + "/words/" + word)
            else: 
                # TODO increment count by 1 
                count[word] = count[word] + 1

        for entry in count:
            try:
                directory = Utils.after_each_character_insert(entry, '/')
                linkDir = "index/%s" % directory
                link = "%s/%s-%s=>%s" % (linkDir, 100000000000000000 - count[entry], count[entry], doc.id)
                os.symlink(doc.id, link)
            except OSError as error: print error, doc.id, "%s/%s-%s=>%s" % (linkDir, 100000000000000000 - count[entry], count[entry], doc.id)


    @staticmethod
    def removeFromIndex(docPath, id):
        wordsDir = docPath + "/words"
        for word in os.listdir(wordsDir):
            directory = Utils.after_each_character_insert(word, '/')
            linkDir = "index/%s" % directory
            link = "%s/%s" % (linkDir, id)
            
            # remove link
            os.remove(link)

            # remove count
            Utils.purge(linkDir, "^.*.=>" + id + "$")

            # remove word
            os.remove("%s/%s" % (wordsDir, word))
    
class Document:
    def __init__(self, id, text):
        self.id = id
        self.text = text


# simple test
if __name__ == '__main__':

    index = Index()
    print "dir is %s" % index.dir
    index.add(Document("test1", "top hat hat"))
    index.add(Document("test2", "top top cat"))





