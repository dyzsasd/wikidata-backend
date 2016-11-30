import pymongo


from wikidata_backend.settings import MONGO


client = pymongo.MongoClient(MONGO['host'], MONGO['port'])

db = client[MONGO['db']]

raw_collection = db[MONGO['collection']['raw']]
entity_collection = db[MONGO['collection']['entity']]
relation_collection = db[MONGO['collection']['relation']]


wiki_link_templates = {
    'enwiki': {
        'template': 'https://en.wikipedia.org/wiki/%s',
        'language': 'en',
    },
    'frwiki': {
        'template': 'https://fr.wikipedia.org/wiki/%s',
        'language': 'fr',
    }
}


def format_wiki_links(sitelinks):
    wiki_links = {}
    for project, template_obj in wiki_link_templates.iteritems():
        if project in sitelinks:
            title = sitelinks[project]['title'].replace(' ', '_')
            wiki_links[template_obj['language']] = (
                template_obj['template'] % title)
    return wiki_links


def format_wiki_titles(sitelinks):
    wiki_titles = {}
    for project, template_obj in wiki_link_templates.iteritems():
        if project in sitelinks:
            title = sitelinks[project]['title'].replace(' ', '_')
            wiki_titles[template_obj['language']] = title
    return wiki_titles


def format_labels(raw_labels):
    return {
        language: value['value']
        for language, value in raw_labels.iteritems()
    }


def format_descriptions(raw_descriptions):
    return {
        language: value['value']
        for language, value in raw_descriptions.iteritems()
    }


def format_aliases(raw_aliases):
    return {
        language: [
            aliase['value'] for aliase in aliases
        ]
        for language, aliases in raw_aliases.iteritems()
    }


def format_entity(raw_obj):
    '''Format wikidata entity object'''

    entity = {
        '_id': raw_obj['_id'],
        'links': format_wiki_links(raw_obj['sitelinks']),
        'wiki_title': format_wiki_titles(raw_obj['sitelinks']),
        'labels': format_labels(raw_obj['labels']),
        'descriptions': format_descriptions(raw_obj['descriptions']),
        'aliases': format_aliases(raw_obj['aliases']),
    }
    return entity


def format_claim_relation(subject, claim):
    mainsnak = claim['mainsnak']
    return {
        '_id': claim['id'],
        'rank': claim['rank'],
        'type': claim['type'],
        'subject': subject,
        'subject_type': 'wikibase-item',
        'object': mainsnak['datavalue']['value'],
        'object_type': mainsnak['datavalue']['type'],
        'relation_id': mainsnak['property'],
        'references': claim.get('references', []),
        'qualifiers': [
            qualifier_item
            for qualifier_items in claim.get('qualifiers', {}).itervalues()
            for qualifier_item in qualifier_items
        ]
    }


cursor = raw_collection.find({})

count = 0

for raw_obj in cursor:
    entity = format_entity(raw_obj)
    _id = entity['_id']
    del entity['_id']
    entity_collection.update_one({'_id': _id}, {'$set': entity}, upsert=True)
    claims = [
        format_claim_relation(_id, raw_claim)
        for claim_type, raw_claims in raw_obj['claims'].iteritems()
        for raw_claim in raw_claims
    ]
    for claim in claims:
        claim_id = claim['_id']
        del claim['_id']
        relation_collection.update_one(
            {'_id': claim_id}, {'$set': claim}, upsert=True)
    count += 1
    if count > 4:
        break
