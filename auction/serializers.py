from django.utils import timezone
from rest_framework import serializers
from .models import Auction, Bid, Category


class AuctionSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    winner_id = serializers.SerializerMethodField()
    payment_kopecks = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = [
            "id",
            "owner_id",
            "category",
            "title",
            "description",
            "budget_kopecks",
            "ends_at",
            "due_at",
            "status",
            "moderation_reason",
            "winner_id",
            "payment_kopecks",
            "closed_at",
        ]
        read_only_fields = ["status", "moderation_reason", "closed_at"]
        extra_kwargs = {
            "title": {"min_length": 5},
            "description": {"min_length": 20, "max_length": 5000},
            "budget_kopecks": {"min_value": 100, "max_value": 10**12},
        }

    def get_winner_id(self, obj):
        return obj.winner_id if obj.status == "closed" else None

    def get_payment_kopecks(self, obj):
        return obj.payment_kopecks if obj.status == "closed" else None

    def validate(self, attrs):
        end = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        due = attrs.get("due_at", getattr(self.instance, "due_at", None))
        if end <= timezone.now() or due <= end:
            raise serializers.ValidationError(
                "Окончание торгов должно быть в будущем, срок работы — позже торгов"
            )
        return attrs


class BidInput(serializers.Serializer):
    amount_kopecks = serializers.IntegerField(min_value=1, max_value=10**12)


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ["id", "auction_id", "amount_kopecks", "created_at"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class DecisionInput(serializers.Serializer):
    reason = serializers.CharField(max_length=2000, allow_blank=False)
