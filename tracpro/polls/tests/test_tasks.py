from tracpro.test.cases import TracProDataTest

from ..tasks import fetch_org_runs


class TestPollTasks(TracProDataTest):

    def setUp(self):
        super(TestPollTasks, self).setUp()
        self.org = self.unicef

    def test_fetch_org_runs(self):
        import ipdb; ipdb.set_trace()
        # TODO: How do I test something that connects to the Temba API?
        # fetch_org_runs(self.org)
        print("test")