from django.test import Client
from django.test import TestCase
from authors.apps.authentication.models import User
import json


class BaseTest(TestCase):

    def setUp(self):
        """ automatically run the function before running other tests"""
        self.test_client = Client()

        self.article_to_create = {
            "article": {
                "title": "hahahhaha hahaha hahah ahhah",
                "body": "<p>this is a body that is here hahahhahaha\n </p>",
                "description": "this is another article hahahhaha"
            }
        }

        self.user_to_login = {
            'user': {
                'email': 'haven.authors@gmail.com',
                'password': 'jakejake@20AA'
            }
        }

        self.user_to_login2 = {
            'user': {
                'email': 'haven.authors2@gmail.com',
                'password': 'jakejake@20AA'
            }
        }

        self.rating_to_create = {
            "article": {
                "rating": 1,
                "review": "the service was really great. I recomend you go there."
            }
        }

        self.rating_lower_than_1 = {
            "article": {
                "rating": 0,
                "review": "the service was really great. I recomend you go there."
            }
        }

        self.rating_greater_than_5 = {
            "article": {
                "rating": 6,
                "review": "the service was really great. I recomend you go there."
            }
        }

        # Create a verified user
        johndoe_user = User.objects.create_user(
            'Aurthurs', 'haven.authors@gmail.com', 'jakejake@20AA')
        johndoe_user.is_verified = True
        johndoe_user.save()

        jonedoe_user = User.objects.create_user(
            'Aurthurs2', 'haven.authors2@gmail.com', 'jakejake@20AA')
        jonedoe_user.is_verified = True
        jonedoe_user.save()

        self.user_logged_in = self.login_user(self.user_to_login)
        self.user_2_logged_in = self.login_user(self.user_to_login2)
        self.create_article = self.create_an_article(self.user_logged_in)
        self.own_article = self.create_an_article(self.user_2_logged_in)

    def login_user(self, user_details_dict):
        """Authenticate the user credentials and login

        Args:
            user_details_dict: a dictionary with email and password of the user.

        Returns: an issued post request to the user Authentication endpoint.
        """
        return self.test_client.post(
            "/api/users/login/", data=json.dumps(user_details_dict),
            content_type='application/json')

    def create_an_article(self, article_owner):
        # log the user in to get auth token
        response = article_owner

        # extrct token from response
        token = response.json()['user']['token']

        # generate an HTTP header with token
        headers = {'HTTP_AUTHORIZATION': 'Token ' + token}

        # send a request to create an article
        return self.test_client.post(
            "/api/articles/", **headers,
            data=json.dumps(self.article_to_create), content_type='application/json')

    def tearDown(self):
        pass


class TestArticles(BaseTest):

    def test_create_article(self):

        response = self.create_article

        #  perform test case test
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()['article']['message'], 'Article created successfully.')


class TestArticleRating(BaseTest):

    def test_create_rating(self):
        """ test if a rating can be created """
        response = self.user_2_logged_in

        # extrct token from response
        token = response.json()['user']['token']

        # generate an HTTP header with token
        headers = {'HTTP_AUTHORIZATION': 'Token ' + token}

        response = self.test_client.post(
            "/api/articles/rate/1", **headers,
            data=json.dumps(self.rating_to_create), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()['article']['message'], 'Article rated successfully.')

    def test_rating_lower_than_1(self):
        """ test if a user can make rating level less than one """

        response = self.user_2_logged_in

        # extrct token from response
        token = response.json()['user']['token']

        # generate an HTTP header with token
        headers = {'HTTP_AUTHORIZATION': 'Token ' + token}

        response = self.test_client.post(
            "/api/articles/rate/1", **headers,
            data=json.dumps(self.rating_lower_than_1), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['errors']['rating'], ['Rating should be in range of 1 to 5.'])

    def test_rating_greater_than_5(self):
        """ test if a user can make rating level greater than five """

        response = self.user_2_logged_in

        # extrct token from response
        token = response.json()['user']['token']

        # generate an HTTP header with token
        headers = {'HTTP_AUTHORIZATION': 'Token ' + token}

        response = self.test_client.post(
            "/api/articles/rate/1", **headers,
            data=json.dumps(self.rating_greater_than_5), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['errors']['rating'], ['Rating should be in range of 1 to 5.'])

    def test_user_rating_twice(self):
        """  test is  a user can rate the same artricle twice """

        response = self.user_2_logged_in

        # extrct token from response
        token = response.json()['user']['token']

        # generate an HTTP header with token
        headers = {'HTTP_AUTHORIZATION': 'Token ' + token}

        self.test_client.post(
            "/api/articles/rate/1", **headers,
            data=json.dumps(self.rating_to_create), content_type='application/json')

        response2 = self.test_client.post(
            "/api/articles/rate/1", **headers,
            data=json.dumps(self.rating_to_create), content_type='application/json')
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(
            response2.json()['errors']['error'], ['You cannot rate an article twice.'])

    def test_if_user_can_rate_own_article(self):
        """ test if a user can rate own articles """

        response = self.user_logged_in

        # extrct token from response
        token = response.json()['user']['token']

        # generate an HTTP header with token
        headers = {'HTTP_AUTHORIZATION': 'Token ' + token}

        response = self.test_client.post(
            "/api/articles/rate/1", **headers,
            data=json.dumps(self.rating_to_create), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['errors']['error'], ['You cannot rate your own article'])