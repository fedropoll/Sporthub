from rest_framework import serializers
from .models import Hall, Club, Review

class HallSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id', 'name', 'address', 'phone', 'working_hours', 'images',
            'advantages', 'size', 'hall_type', 'coating', 'inventory',
            'price_per_hour', 'dressing_room', 'lighting', 'shower',
            'capacity', 'latitude', 'longitude', 'average_rating',
            'review_count', 'video_url'
        ]
        ref_name = 'MainHall'



class ClubSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    hall_info = HallSerializer(source='hall', read_only=True)

    class Meta:
        model = Club
        fields = [
            'id', 'name', 'description', 'coach', 'contact_phone',
            'training_schedule', 'age_groups', 'price_per_month',
            'hall', 'hall_info', 'logo', 'average_rating',
            'review_count', 'video_url'
        ]
        extra_kwargs = {
            'hall': {'write_only': True}
        }
        ref_name = 'MainClub'  # уникальное имя для Swagger


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id', 'author', 'hall', 'club', 'rating', 'text',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
        ref_name = 'MainReview'  # чтобы не конфликтовать

    def validate(self, data):
        if not data.get('hall') and not data.get('club'):
            raise serializers.ValidationError(
                "Должен быть указан либо зал, либо клуб"
            )
        return data


class HallDetailSerializer(HallSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(HallSerializer.Meta):
        fields = HallSerializer.Meta.fields + ['reviews']


class ClubDetailSerializer(ClubSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(ClubSerializer.Meta):
        fields = ClubSerializer.Meta.fields + ['reviews']
