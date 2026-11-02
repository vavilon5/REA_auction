from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)


class Auction(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        REVIEW = "review"
        REJECTED = "rejected"
        OPEN = "open"
        CLOSED = "closed"
        PAUSED = "paused"

    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="auctions")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=150)
    description = models.TextField()
    budget_kopecks = models.PositiveBigIntegerField()
    ends_at = models.DateTimeField()
    due_at = models.DateTimeField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    moderation_reason = models.TextField(blank=True)
    winner = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="wins"
    )
    payment_kopecks = models.PositiveBigIntegerField(null=True)
    closed_at = models.DateTimeField(null=True)

    class Meta:
        permissions = [("moderate_auction", "Модерировать аукционы")]
        indexes = [models.Index(fields=["status", "ends_at"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(budget_kopecks__gte=100), name="budget_min_ruble"
            ),
            models.CheckConstraint(
                condition=Q(due_at__gt=models.F("ends_at")), name="due_after_auction"
            ),
        ]


class Assignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Назначена"
        IN_PROGRESS = "in_progress", "В работе"
        ON_REVIEW = "on_review", "На проверке"
        COMPLETED = "completed", "Завершена"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
    )
    
    auction = models.OneToOneField(
        Auction,
        on_delete=models.PROTECT,
        related_name="assignment",
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="customer_assignments",
    )
    executor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="executor_assignments",
    )
    price_kopecks = models.PositiveBigIntegerField()
    due_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(price_kopecks__gte=1),
                name="assignment_price_positive",
            ),
            models.CheckConstraint(
                condition=~Q(customer=models.F("executor")),
                name="assignment_different_parties",
            ),
        ]   


class Submission(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Ожидает проверки"
        ACCEPTED = "accepted", "Принят"
        RETURNED = "returned", "Возвращён"

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    text = models.TextField(max_length=10000)
    version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    review_comment = models.TextField(
        max_length=2000,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="reviewed_submissions",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["version"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "version"],
                name="unique_submission_version",
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1),
                name="submission_version_positive",
            ),
        ]
      

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.PROTECT, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.PROTECT)
    amount_kopecks = models.PositiveBigIntegerField()
    idempotency_key = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["auction", "bidder"], name="one_bid_per_person"
            ),
            models.UniqueConstraint(
                fields=["auction", "bidder", "idempotency_key"],
                name="unique_request_key",
            ),
            models.CheckConstraint(
                condition=Q(amount_kopecks__gte=1), name="bid_positive"
            ),
        ]


class Event(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.PROTECT)
    actor = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=40)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
