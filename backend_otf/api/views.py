from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Usuario
from .serializers import (
    LoginSerializer,
    ProfilePutSerializer,
    RegisterSerializer,
    UserResponseSerializer,
)


def index(request):
    return HttpResponse("Hello, world. You're at the denuncias index lmao.")


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserResponseSerializer(user).data,
            'token': token.key,
        })


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({
            'user': UserResponseSerializer(user).data,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)


class ProfileUpdateView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = ProfilePutSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['put']  # solo PUT, el frontend usa multipart

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        return Response(UserResponseSerializer(updated_user).data)
