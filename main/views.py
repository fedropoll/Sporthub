from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import RegisterSerializer, RequestPasswordResetSerializer, ConfirmPasswordResetSerializer

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

class RequestPasswordResetAPIView(generics.CreateAPIView):
    serializer_class = RequestPasswordResetSerializer

class ConfirmPasswordResetAPIView(generics.CreateAPIView):
    serializer_class = ConfirmPasswordResetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Пароль успешно изменён"}, status=status.HTTP_200_OK)
