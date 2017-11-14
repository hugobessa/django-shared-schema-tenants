from rest_framework import viewsets, permissions
from .models import Lecture
from .serializers import LectureSerializer


class LectureViewSet(viewsets.ModelViewSet):
    serializer_class = LectureSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Lecture.objects.all()
