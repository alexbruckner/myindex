#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, string, shutil, glob, json

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

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
		self.matches = set()

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

	def match(self, match):
		self.matches.add(match)
		return self

	def __hash__(self):
		return hash(self.id)

	def __eq__(self, another):
		return hash(self) == hash(another)


class Query(object):
	def __init__(self, query, fields = (), filter = (), paging = ()):
		self.query = query
		self.fields = fields
		self.filter = filter
		self.paging = paging

	def __repr__(self):
		return "%s [fields = %s, filter = %s, paging = %s]" % (self.query, self.fields, self.filter, self.paging)

# TODO
class SearchResult(object):
	def __init__(self, query, result = {}):
		self.query = query
		self.result = result

	def __repr__(self):
		return "%s %s" % (self.query, self.result)


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

	def search(self, query, fields = (), filters = (), paging = ()):
		pathified_query = Utils.pathify(query)
		
		result = set()
		specific_fields = len(fields) > 0
		index_dirs = []
		specific_filters = len(filters) > 0
		filter_list = set()
		specific_page = len(paging) > 0

		if specific_filters:
			for filter in filters:
				filter_result = self.search(query = filter[1], fields = (filter[0],))
				if len(filter_list) > 0:
					filter_list = filter_list.intersection(filter_result.result)
				else:
					filter_list = set(filter_result.result)

		if specific_fields:
			for field in fields:
				index_dirs.append("%s/%s/#%s/*" % (self.index_dir, pathified_query, field))
		else:    
			index_dirs.append("%s/%s/#*/*" % (self.index_dir, pathified_query))
			
		file_list = []    
		for index_dir in index_dirs:
			file_list += glob.glob(index_dir)

		if specific_page:
			page_start = paging[0]
			page_size = paging[1]

			page_count_start = page_start * page_size
			page_count_end = page_count_start + page_size

		tmp_refs = {}

		i = 0
		for path in file_list:
				first = path.index("#") + 1
				second = path.index("/", first)
				match = path[first:second]
				doc_id = path[second + 1 :]
				if not specific_filters or (doc_id in filter_list):

					if doc_id in tmp_refs:
						index_doc = tmp_refs[doc_id]
					else:
						index_doc = IndexDocument(self, doc_id)
						tmp_refs[doc_id] = index_doc
						
						if specific_page: 
							i  = i + 1

							if len(result) >= page_size: 
								break
							
							if i <= page_count_start:
								continue

						result.add(index_doc)
							

					index_doc.match(match)

		tmp_refs.clear()

		return SearchResult(Query(query, fields, filters, paging), result)

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

	def load(self, doc_id, lazy = True):
		return IndexDocument(self, doc_id, lazy = lazy)

	def json(self, doc_id):
		return IndexDocument(self, doc_id, lazy = False).json()

	def doc(self, json_str):
		data = json.loads(json_str)
		doc_id = data[0]
		fields = data[1]
		doc = IndexDocument(self, doc_id, lazy = False)
		for field in data[1]:
			doc.vals[field] = data[1][field]
		return doc

	def reset(self):
		shutil.rmtree(self.data_dir)
		shutil.rmtree(self.index_dir)

# simple test
if __name__ == '__main__':
	
	index = Index()

	index.reset()

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

	print index.load("test", lazy = True).get('text')

	print "json: ", index.json("test")
	print "doc:  ", index.doc(index.json("test"))

	print index.search("a", paging = (0, 3))
	print index.search("a", paging = (0, 1))
	print index.search("a", paging = (1, 1))
	print index.search("a", paging = (2, 1))

	# TODO highlight = False, size = 300, paging = -1, start = 0 multiple words in query

