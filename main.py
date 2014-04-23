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
		if not os.path.exists(directory):
    			os.makedirs(directory)



class Index:
	def __init__(self, dir = os.getcwd()):
		self.dir = dir

	def add(self, doc):
		Utils.makedirs("data", doc.id)
		with open("data/%s/text" % doc.id, 'w') as f:
			f.write(doc.text)

		for word in doc.text.split():
			directory = Utils.after_each_character_insert(word, '/')
			Utils.makedirs("index", directory)

			link = "%s/data/%s" % (self.dir, doc.id)
			docPath = "index/%s/%s" % (directory, doc.id)
			if not os.path.exists(link):
				os.symlink(link, docPath)



    
class Document:
	def __init__(self, id, text):
		self.id = id
		self.text = text


# simple test
if __name__ == '__main__':

	index = Index()
	print "dir is %s" % index.dir
	index.add(Document("test1", "top hat"))
	index.add(Document("test2", "top cat"))





