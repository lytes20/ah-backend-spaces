from rest_framework import status
from rest_framework.generics import (
    RetrieveUpdateAPIView, CreateAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.template.defaultfilters import slugify
import uuid
from ..authentication.backends import JWTAuthentication
from ..authentication.models import User
from . models import Rating as DbRating

from .renderers import (
    ArticlesJSONRenderer, CommentJSONRenderer, RatingJSONRenderer
)

from .serializers import (
    CreateArticleAPIViewSerializer, RatingArticleAPIViewSerializer,
    CommentArticleAPIViewSerializer, ChildCommentSerializer,
    LikeArticleAPIViewSerializer, FavouriteArticleAPIViewSerializer
)


class CreateArticleAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ArticlesJSONRenderer,)
    serializer_class = CreateArticleAPIViewSerializer

    def post(self, request):
        article = request.data.get('article', {})

        # decode user token and return its value
        user_data = JWTAuthentication().authenticate(request)

        article["user_id"] = user_data[1]

        # create a an article slug fron title
        try:
            slug = slugify(article["title"]).replace("_", "-")
            slug = slug + "-" + str(uuid.uuid4()).split("-")[-1]
            article["slug"] = slug
        except KeyError:
            pass

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.

        serializer = self.serializer_class(data=article)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data["message"] = "Article created successfully."

        return Response(data, status=status.HTTP_201_CREATED)


class RateArticleAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (RatingJSONRenderer,)
    serializer_class = RatingArticleAPIViewSerializer

    def post(self, request, article_id):
        Rating = request.data.get('Rating', {})

        # Add the article id to rating to be made
        Rating["article_id"] = article_id

        # decode user token and return its value
        user_data = JWTAuthentication().authenticate(request)

        # get id of the user rating an article
        Rating["user_id"] = user_data[1]

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.

        serializer = self.serializer_class(data=Rating)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data["message"] = "Article rated successfully."

        # get average rating
        rating_data = DbRating.objects.filter(
            article_id=article_id).values('rating')
        empty_lst = []
        for rating in rating_data:
            empty_lst.append(rating["rating"])

        # callculate average rating
        average_rating = sum(empty_lst) / len(empty_lst)
        data["average_rating"] = average_rating

        # append success message to output
        data["message"] = "Article rated successfully."

        return Response(data, status=status.HTTP_201_CREATED)


class CommentArticleAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (CommentJSONRenderer,)

    # serailizer class to be used for parent comment
    # A parent comment is a comment that can have threaded comments attached to it
    serializer_class_a = CommentArticleAPIViewSerializer

    # serializer class to be used for child comment
    # A child comment is a thread to a main comment
    serializer_class_b = ChildCommentSerializer

    def post(self, request, article_id):
        comment = request.data.get('comment', {})

        try:
            # check if a parent id is suplied
            # if supplied add the parent id to comment that
            # is supposed to be verified and change seralizer class method
            comment["parent_id"] = comment["parent_id"]
            serializer_class = self.serializer_class_b
        except KeyError:
            # if no comment parent id is supplied, use the below serializer class instance
            serializer_class = self.serializer_class_a

        # Add the article id to rating to be made
        comment["article_id"] = article_id

        # decode user token and return its value
        user_data = JWTAuthentication().authenticate(request)

        # get id of the user rating an article
        comment["author"] = user_data[1]

        # Notice here that we do not call `serializer.save()` like we did for
        # the registration endpoint. This is because we don't actually have
        # anything to save. Instead, the `validate` method on our serializer
        # handles everything we need.

        serializer = serializer_class(data=comment)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        data["message"] = "Comment created successfully."

        return Response(data, status=status.HTTP_201_CREATED)


class LikeArticleAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ArticlesJSONRenderer,)
    serializer_class = LikeArticleAPIViewSerializer

    def get(self, request, article_id):

        return Response({"error": "method GET not allowed"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, article_id):
        """ This function is handling requests for creating a like

        Args:
            request: contains more details about the request made
            article_id: id of the article to be liked

        Return: Response showing that the article was liked
        """

        like = request.data.get('article', {})

        user_data = JWTAuthentication().authenticate(request)

        like["user_id"] = user_data[1]

        like["article_id"] = article_id

        serializer = self.serializer_class(data=like)
        serializer.is_valid(raise_exception=True)

        result = serializer.perform_save(like)

        return Response(result)

    def put(self, request, article_id):
        """ This function is handling requests for updating a like

        Args:
            request: contains more details about the request made
            article_id: id of the article to check for when updating

        Return: Response showing that the article was updated
        """
        like = request.data.get('article', {})

        user_data = JWTAuthentication().authenticate(request)

        like["user_id"] = user_data[1]

        like["article_id"] = article_id

        serializer = self.serializer_class(data=like)
        serializer.is_valid(raise_exception=True)

        result = serializer.perform_update(like)

        return Response(result)

    def delete(self, request, article_id):
        """ This function is handling requests for deleting a like

        Args:
            request: contains more details about the request made
            article_id: id of the article to be deleted

        Return: Response showing that the article was deleted
        """
        serializer_data = request.data.get('article', {})

        user_data = JWTAuthentication().authenticate(request)

        serializer_data["user_id"] = user_data[1]
        serializer_data["article_id"] = article_id

        serializer = self.serializer_class(
            data=serializer_data, partial=True)
        serializer.is_valid(raise_exception=True)

        result = serializer.perform_delete(serializer_data)

        return Response(result, status=status.HTTP_200_OK)


class FavouriteArticleAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (ArticlesJSONRenderer,)
    serializer_class = FavouriteArticleAPIViewSerializer

    def post(self, request, article_id):
        """ This function is handling requests for creating a like

        Args:
            request: contains more details about the request made
            article_id: id of the article to be liked

        Return: Response showing that the article was liked
        """

        like = request.data.get('article', {})

        user_data = JWTAuthentication().authenticate(request)

        like["user_id"] = user_data[1]

        like["article_id"] = article_id

        serializer = self.serializer_class(data=like)
        serializer.is_valid(raise_exception=True)
        result = serializer.perform_save(like)
        return Response(result)

    def delete(self, request, article_id):
        """ This function is handling requests for deleting a like

        Args:
            request: contains more details about the request made
            article_id: id of the article to be deleted

        Return: Response showing that the article was deleted
        """
        serializer_data = request.data.get('article', {})

        user_data = JWTAuthentication().authenticate(request)

        serializer_data["user_id"] = user_data[1]
        serializer_data["article_id"] = article_id

        serializer = self.serializer_class(
            data=serializer_data, partial=True)
        serializer.is_valid(raise_exception=True)

        result = serializer.perform_delete(serializer_data)

        return Response(result, status=status.HTTP_200_OK)
