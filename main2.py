#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, string, shutil, glob

class Utils:
    
    @staticmethod
    def pathify(word, char = '/'):        
        return char.join([str(ord(c)) for c in word.lower()])

    @staticmethod
    def makedirs(directory):
        ok = False
        if not os.path.exists(directory):
                os.makedirs(directory)
                ok = True
        return ok

    @staticmethod
    def toId(s):
        return re.sub('[\W_]+', '-', s)

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

class IndexDocument(object):
    def __init__(self, index, id):
        self.index = index
        self.id = id

    def __repr__(self):
        return "<Doc: %s>" % self.id


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
    	# add data
    	doc_dir = "%s/%s" % (self.data_dir, doc.id)
    	Utils.makedirs(doc_dir)
    	for field in doc.vals:
    		field_file = "%s/%s" % (doc_dir, field)	
    		with open(field_file, 'w') as f:
    			f.write(doc.vals[field])	# TODO do not store data, just index on id as an option?
    			self.index(doc.id, doc_dir, field, doc.vals[field])


    def index(self, doc_id, doc_dir, field, value):
    	# strip html
    	words = re.sub('<[^<]+?>', ' ', value)

    	# strip punctuation
    	words = words.translate(string.maketrans("",""), string.punctuation)

    	for word in words.split(): 
    		if len(word) > 0:
    			index_dir = "%s/%s/#%s" % (self.index_dir, Utils.pathify(word), field)
    			Utils.makedirs(index_dir)
    			link = "%s/%s" % (index_dir, doc_id)
    			try:
    				if not os.path.exists(link):    # TODO hit count 
	    				os.symlink(doc_dir, link)
    			except OSError as error: print error, link

    def search(self, query):
    	index_dir = "%s/%s/#*/*" % (self.index_dir, Utils.pathify(query))
    	result = {}
        for path in glob.glob(index_dir):
            first = path.index("#") + 1
            second = path.index("/", first)
            match = path[first:second]
            if not match in result:
                result[match] = []
            result[match].append(IndexDocument(self, path[second + 1 :]))
        return result

    def addDir(self, dir):
        dir = os.path.abspath(dir)
        for root, dirs, files in os.walk(dir, topdown=False):
            for file in files:
                self.addFile(os.path.join(root, file))

    def addFile(self, file): 
    	file = os.path.abspath(file)
        doc_id = Utils.toId(file)
        doc_dir = "%s/%s" % (self.data_dir, doc_id)
        Utils.makedirs(doc_dir)

        shutil.copyfile(file, "%s/text" % doc_dir)
        value = None
        with open(file, 'r') as f:
        	value = f.read()

        self.index(doc_id, doc_dir, 'text', value)


# simple test
if __name__ == '__main__':
	
	shutil.rmtree('./data')
	shutil.rmtree('./index')

	doc = Document("test", "a à <p>para,     gráph. ab </p>")
	doc2 = Document("test2", "à á").add("type", "a")

	index = Index()

	index.add(doc)
	index.add(doc2)

	# index.addDir('./test')

	print "a", index.search("a")
	print "à", index.search("à")
	print "á", index.search("á")



