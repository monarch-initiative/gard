"""Tests

How to run: python -m unittest discover
"""
import os
import sys
import unittest
from pathlib import Path

import pandas as pd

TEST_DIR = os.path.dirname(__file__)
PROJECT_ROOT = Path(TEST_DIR).parent
sys.path.insert(0, str(PROJECT_ROOT))

TEST_INPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
TEST_INPUT_RELEAES_DIR = os.path.join(TEST_INPUT_DIR, 'release')


class TestGardMondoExactSssom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """setUp"""
        gard_mondo_exact_sssom_path = os.path.join(TEST_INPUT_RELEAES_DIR, 'gard-mondo-exact_curation.sssom.tsv')
        cls.df = pd.read_csv(gard_mondo_exact_sssom_path, sep='\t', comment='#')

    def test_dup_edges(self):
        """Test that there are no duplicate edges"""
        dup_edges = self.df[self.df.duplicated(subset=['subject_id', 'object_id'])]
        self.assertEqual(len(dup_edges), 0, msg=f'Found {len(dup_edges)} duplicate edges')

    # todo: This fails. I think not because of my code, but because of our mapping strategy. Need @Nico feedback
    def test_mondo_ids(self):
        """Test that there are no duplicate Mondo IDs"""
        dup_mondo_df = self.df[self.df.duplicated(subset=['object_id'])].sort_values(['object_id'])
        dup_mondo_ids = dup_mondo_df['object_id'].unique()
        self.assertEqual(len(dup_mondo_ids), 0, msg=f'Found {len(dup_mondo_ids)} duplicate mondo IDs')

    def test_gard_ids(self):
        """Test that there are no duplicate Mondo IDs"""
        dup_gard_df = self.df[self.df.duplicated(subset=['subject_id'])].sort_values(['subject_id'])
        dup_gard_ids = dup_gard_df['subject_id'].unique()
        self.assertEqual(len(dup_gard_ids), 0, msg=f'Found {len(dup_gard_ids)} duplicate mondo IDs')


class TestGardMondoSssom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """setUp"""
        # gard_mondo_exact_sssom_path = os.path.join(TEST_INPUT_RELEAES_DIR, 'gard-mondo_curation.sssom.tsv')
        # cls.df = pd.read_csv(gard_mondo_exact_sssom_path, sep='\t', comment='#')
        pass

    # todo: this will still have duplicates until we algorithmically dedupe
    # def test_dup_edges(self):
    #     """Test that there are no duplicate edges"""
    #     dup_edges = self.df[self.df.duplicated(subset=['subject_id', 'object_id'])]
    #     self.assertEqual(len(dup_edges), 0, msg=f'Found {len(dup_edges)} duplicate edges')

    # todo: should there be no duplicates for these? even after we algorithmically dedupe?
    # def test_mondo_ids(self):
    #     """Test that there are no duplicate Mondo IDs"""
    #     dup_mondo_df = self.df[self.df.duplicated(subset=['object_id'])].sort_values(['object_id'])
    #     dup_mondo_ids = dup_mondo_df['object_id'].unique()
    #     self.assertEqual(len(dup_mondo_ids), 0, msg=f'Found {len(dup_mondo_ids)} duplicate mondo IDs')

    # todo: this will still have duplicates until we algorithmically dedupe
    # def test_gard_ids(self):
    #     """Test that there are no duplicate Mondo IDs"""
    #     dup_gard_df = self.df[self.df.duplicated(subset=['subject_id'])].sort_values(['subject_id'])
    #     dup_gard_ids = dup_gard_df['subject_id'].unique()
    #     self.assertEqual(len(dup_gard_ids), 0, msg=f'Found {len(dup_gard_ids)} duplicate GARD IDs')


if __name__ == '__main__':
    unittest.main()
