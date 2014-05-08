#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, string, shutil, glob, json

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
	def __init__(self, index, id, lazy = True):
		self.index = index
		self.id = id
		self.doc_dir = '%s/%s' % (self.index.data_dir, self.id)
		self.vals = {}
		self.lazy = lazy
		if not lazy:
			self.load()

	def __repr__(self):
		return "<Doc: %s>" % self.id

	def fields(self):
		return os.listdir(self.doc_dir)

	def get(self, field):
		if not field in self.vals:
			# load
			field_file = "%s/%s" % (self.doc_dir, field)
			with open(field_file, 'r') as f:
				self.vals[field] = f.read()

		return self.vals[field]

	def load(self):
		for field in self.fields():
			self.get(field)

	def json(self):
		if self.lazy:
			self.load()
		return json.dumps((self.id, self.vals), ensure_ascii=False)

class Query(object):
	def __init__(self, query, fields = (), filter = ()):
		self.query = query
		self.fields = fields
		self.filter = filter

	def __repr__(self):
		return "%s [fields = %s, filter = %s]" % (self.query, self.fields, self.filter)

# TODO
class SearchResult(object):
	def __init__(self, query, result = {}):
		self.query = query
		self.result = result

	def __repr__(self):
		return "%s %s" % (self.query, self.result)

	def doc_ids(self):
		try:
			return [ doc.id for doc in self.result.values()[0]]
		except: 
			return []

	def docs(self):
		return self.result.values()[0]

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

		encountered = {}

		for word in words.split(): 
			if len(word) > 0:
				index_dir = "%s/%s/#%s" % (self.index_dir, Utils.pathify(word), field)
				Utils.makedirs(index_dir)
				link = "%s/%s" % (index_dir, doc_id)
				if link not in encountered:
					os.symlink(doc_dir, link)
					encountered[link] = 1

		encountered.clear()

	def search(self, query, fields = (), filters = ()):
		pathified_query = Utils.pathify(query)
		
		result = {}
		specific_fields = len(fields) > 0
		index_dirs = []
		specific_filters = len(filters) > 0
		filter_list = set()

		if specific_filters:
			for filter in filters:
				filter_result = self.search(query = filter[1], fields = (filter[0],))
				if len(filter_list) > 0:
					filter_list = filter_list.intersection(filter_result.doc_ids())
				else:
					filter_list = set(filter_result.doc_ids())

		if specific_fields:
			for field in fields:
				index_dirs.append("%s/%s/#%s/*" % (self.index_dir, pathified_query, field))
		else:    
			index_dirs.append("%s/%s/#*/*" % (self.index_dir, pathified_query))
			
		file_list = []    
		for index_dir in index_dirs:
			file_list += glob.glob(index_dir)

		for path in file_list:
			first = path.index("#") + 1
			second = path.index("/", first)
			match = path[first:second]
			doc_id = path[second + 1 :]
			if not specific_filters or (doc_id in filter_list):
				if not match in result:
					result[match] = []
				result[match].append(IndexDocument(self, doc_id))
		return SearchResult(Query(query, fields, filters), result)

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

	def load(self, index_doc, lazy = True):
		return IndexDocument(self, index_doc, lazy = lazy)

# simple test
if __name__ == '__main__':
	
	shutil.rmtree('./data')
	shutil.rmtree('./index')

	index = Index()

	index.add(Document("test", "a à <p>para,     gráph. ab </p>"))
	index.add(Document("test2", "à á").add("type", "a").add("type2", "b"))
	index.add(Document("test3", "a b c").add("muh", "a b c"))

	# index.addDir('./test')

	print index.search("a")
	print index.search("à")
	print index.search("á")


	print index.search("a", fields = ('text',))

	print index.search("a", filters = (('type', 'a'), ('type2', 'b')))
	print index.search("a", filters = (('type', 'a'), ('type2', 'c')))

	print index.load("test").get('text')

	print "json: ", index.load("test").json()

	# TODO highlight = False, size = 300, paging = -1, start = 0 multiple words in query

