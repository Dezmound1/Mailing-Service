import factory

from mailings.models import MailingRecord


class MailingRecordFactory(factory.django.DjangoModelFactory):
    """Factory for creating MailingRecord test instances."""

    class Meta:
        model = MailingRecord

    external_id = factory.Sequence(lambda n: f"ext-{n}")
    user_id = factory.Sequence(lambda n: f"user-{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.user_id}@example.com")
    subject = factory.Sequence(lambda n: f"Subject {n}")
    message = factory.Sequence(lambda n: f"Message body {n}")
