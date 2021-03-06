import json
from decimal import Decimal

from payments import PaymentStatus, RedirectNeeded
from payments.core import BasicProvider
from .forms import ModalPaymentForm
import razorpay
import razorpay.errors


class RazorPayProvider(BasicProvider):

    form_class = ModalPaymentForm

    def __init__(
            self,
            public_key, secret_key,
            image='', name='', prefill=False, **kwargs):

        self.secret_key = secret_key
        self.public_key = public_key
        self.image = image
        self.name = name
        self.prefill = prefill
        self.razorpay_client = razorpay.Client(auth=(public_key, secret_key))

        super(RazorPayProvider, self).__init__(**kwargs)

    def get_form(self, payment, data=None):
        if payment.status == PaymentStatus.WAITING:
            payment.change_status(PaymentStatus.INPUT)
            
        form = self.form_class(
            data=data, payment=payment, provider=self)

        if form.is_valid():
            raise RedirectNeeded(payment.get_success_url())
        return form

    def charge(self, transaction_id, payment):
        amount = int(payment.total * 100)
        charge = self.razorpay_client.payment.capture(transaction_id, amount)
        return charge

    def refund(self, payment, amount=None):
        amount = int((amount or payment.captured_amount) * 100)
        try:
            refund = self.razorpay_client.payment.refund(
                payment.transaction_id, amount)
        except razorpay.errors.BadRequestError as exc:
            raise ValueError(str(exc))
        refunded_amount = Decimal(refund['amount']) / 100
        payment.attrs.refund = json.dumps(refund)
        return refunded_amount
