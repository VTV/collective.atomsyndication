# -*- coding: utf-8 -*-

import unittest2 as unittest

import logging
import sys

from zope.publisher.browser import TestRequest

from Products.CMFCore.utils import getToolByName

from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles

try:
    # Try to get the new collection type
    import plone.app.collection
    HAS_COLLECTION = True
except:
    HAS_COLLECTION = False

from collective.atomsyndication import atom
from collective.atomsyndication.testing import INTEGRATION_TESTING

logging.basicConfig()
logger = logging.getLogger('collective.atomsyndication')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.debug(u'\nBegin collective.syndication LOG')

PROJECTNAME = 'collective.atomsyndication'
CONTENT_STRUCTURE = [dict(type='News Item',
                          id='news-1',
                          title=u"News Article Number One",
                          description=u"A brief description about the\
                                  artcile, explaining things\
                                  about stuff."
                                  ),
                     dict(type='News Item',
                          id='news-2',
                          title=u"News Article Number Two",
                          description=u"A brief description about the\
                                  artcile, explaining things\
                                  about stuff."),
                     dict(type='News Item',
                          id='news-3',
                          title=u"News Article Number One",
                          description=u"A brief description about the\
                                  artcile, explaining things\
                                  about stuff."
                                  ),
                    ]
if HAS_COLLECTION:
    CONTENT_STRUCTURE.append(dict(type='Collection',
                                  id='topic-1',
                                  title=u"A Collection of Articles",
                                  description=u"A brief description about the\
                                          artcile, explaining things\
                                          about stuff."))
else:
    CONTENT_STRUCTURE.append(dict(type='Topic',
                                  id='topic-1',
                                  title=u"A Collection of Articles",
                                  description=u"A brief description about the\
                                          artcile, explaining things\
                                          about stuff."))


class TestSetup(unittest.TestCase):
    """ Checks instalation of this product """

    layer = INTEGRATION_TESTING

    def populateSite(self, container, contents=CONTENT_STRUCTURE):
        portal = self.layer['portal']
        syndication_tool = getToolByName(portal, 'portal_syndication')
        setRoles(container, TEST_USER_ID, ['Manager'])
        login(container, TEST_USER_NAME)
        for item in contents:
            container.invokeFactory(item["type"],
                                    id=item["id"],
                                    title=item["title"],
                                    description=item["description"],
                                    )
            container[item["id"]].reindexObject()
            if item["type"] == "Topic":
                colec_obj = container[item["id"]]
                type_crit = colec_obj.addCriterion('Type', 'ATPortalTypeCriterion')
                type_crit.setValue('News Item')
                if not syndication_tool.isSyndicationAllowed(colec_obj):
                    syndication_tool.enableSyndication(colec_obj)

            if item["type"] == "Collection":
                colec_obj = container[item["id"]]

                query = [{'i': 'portal_type',
                          'o': 'plone.app.querystring.operation.selection.is',
                          'v': ['News Item']}]

                colec_obj.query = query
                if not syndication_tool.isSyndicationAllowed(colec_obj):
                    syndication_tool.enableSyndication(colec_obj)

        setRoles(container, TEST_USER_ID, ['Member'])

    def test_atom_installed(self):
        portal = self.layer['portal']
        portal_quickinstaller = portal.portal_quickinstaller
        self.failUnless(portal_quickinstaller.isProductInstalled(PROJECTNAME),
                                            '%s not installed' % PROJECTNAME)

    def test_root_atom_enabled(self):
        portal = self.layer['portal']
        request = self.layer['request']
        #self.loginAsPortalOwner()
        self.populateSite(portal)
        req = TestRequest()
        #view = getMultiAdapter((portal, request), name=u"atom.xml")
        view = atom.RootAtomFeedView(portal, None)
        #view = self.portal.restrictedTraverse("atom.xml")
        view.update()

        logger.debug(u"\nQuery: %s" % view.query)
        logger.debug(u"\nCatalog search: %s" % view.query_catalog(view.query))
        logger.debug(u"\nResults: %s" % view.results)
        logger.debug(u"\nFiltered: %s" % view.filtered)
        rendered = view.render()
        logger.debug(u"\nView: %s" % rendered)