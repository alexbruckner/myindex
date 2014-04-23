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

        # add documen to data dir
        Utils.makedirs("data", doc.id)
        with open("data/%s/text" % doc.id, 'w') as f:
            f.write(doc.text)

        # add words to index (ie create a link in word folder to data dir/doc.id)
        for word in doc.text.split():
            directory = Utils.after_each_character_insert(word, '/')
            Utils.makedirs("index", directory)

            docPath = "%s/data/%s" % (self.dir, doc.id)
            link = "index/%s/%s" % (directory, doc.id)
            if not os.path.exists(link):
                os.symlink(docPath, link)
            else: 
                print "to do: increment count from 0 if data was modified: " + link + ", for word: " + word


    
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





