#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

class Utils:
    
    @staticmethod
    def pathify(word, char = '/'):        
        return char.join([str(ord(c)) for c in word])

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

    	# index data  



    def search(self, query):
    	None	


# simple test
if __name__ == '__main__':

	import shutil
	shutil.rmtree('./data')
	shutil.rmtree('./index')

	doc = Document("test", "a à")
	doc2 = Document("test2", "à á")


	index = Index()

	index.add(doc)
	index.add(doc2)

	print "a", index.search("a")
	print "à", index.search("à")
	print "á", index.search("á")



