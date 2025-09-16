from rest_framework import serializers
from users.models import Hall, Club, Review

class HallSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id', 'title', 'sport', 'description', 'address',
            'price_per_hour', 'size', 'count', 'type', 'coating', 'inventory',
            'has_locker_room', 'has_lighting', 'has_shower', 'images',
            'video_url', 'average_rating', 'review_count'
        ]
        ref_name = 'MainHall'





class ClubSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    hall_info = HallSerializer(source='hall', read_only=True)

    class Meta:
        model = Club
        fields = [
            'id', 'title', 'description', 'coach', 'contact_phone',
            'training_schedule', 'age_groups', 'price_per_month',
            'hall', 'hall_info', 'logo', 'average_rating',
            'review_count', 'video_url'
        ]
        extra_kwargs = {'hall': {'write_only': True}}
        ref_name = 'MainClub'



class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'hall', 'club', 'rating', 'text',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
        ref_name = 'MainReview'



class HallDetailSerializer(HallSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(HallSerializer.Meta):
        fields = HallSerializer.Meta.fields + ['reviews']


class ClubDetailSerializer(ClubSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(ClubSerializer.Meta):
        fields = ClubSerializer.Meta.fields + ['reviews']

from rest_framework import serializers
from users.models import Review

class AdminReviewSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    trainer_name = serializers.CharField(source='trainer.first_name', read_only=True)
    club_name = serializers.CharField(source='club.title', read_only=True)

    def get_user_info(self, obj):
        return {
            'username': obj.user.username,
            'email': obj.user.email
        }

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_info', 'trainer', 'trainer_name',
            'club', 'club_name', 'text', 'rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_info', 'trainer_name', 'club_name', 'created_at']
        ref_name = 'AdminReview'
