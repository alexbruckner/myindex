import os

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
            wordsDir = docPath + "/words"
            for word in os.listdir(wordsDir):
                directory = Utils.after_each_character_insert(word, '/')
                linkDir = "index/%s" % directory
                link = "%s/%s" % (linkDir, doc.id)
                # remove link
                os.remove(link)
                # remove word
                os.remove("%s/%s" % (wordsDir, word))
                

        # add words to index (ie create a link in word folder to data dir/doc.id)
        for word in doc.text.split():
            directory = Utils.after_each_character_insert(word, '/')
            Utils.makedirs("index", directory)

            linkDir = "index/%s" % directory
            link = "%s/%s" % (linkDir, doc.id)
            
            if not os.path.exists(link):
                # symlink document match back to document [index -> data]
                os.symlink(docPath, link)
                # symlink document word to index location [data -> index]
                os.symlink("%s/%s" % (self.dir, linkDir), docPath + "/words/" + word)
            else: 
                print "to do: increment count from 1 if data was modified: " + link + ", for word: " + word
    
class Document:
    def __init__(self, id, text):
        self.id = id
        self.text = text


# simple test
if __name__ == '__main__':

    index = Index()
    print "dir is %s" % index.dir
    index.add(Document("test1", "top hat hat"))
    index.add(Document("test2", "top cat"))





