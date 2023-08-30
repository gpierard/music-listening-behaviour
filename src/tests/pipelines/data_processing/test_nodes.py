
# tests/pipelines/inventory/test_nodes.py
class TestProcessingNodes:
    def test_unique_userids(self, track_sessions, userid_profiles):
        nb_distinct_users = track_sessions["userid"].drop_duplicates().shape[0]
        # nb_unique_users = 992
        assert nb_distinct_users==len(userid_profiles['#id'].drop_duplicates())

