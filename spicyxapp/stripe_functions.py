from datetime import datetime
from datetime import timedelta
import time
from django.utils import timezone
import stripe
from django.conf import settings
from spicyxapp import models
from .functions import createPresignedUrl
import requests
import os

stripe.api_key = settings.STRIPE_SECRET_API_KEY


def docs_generateNewsPresignedUrls():
    docs = models.CreatorsRequest.objects.filter(status='pending')
    bucket_name = settings.BUCKET_NAME
    for doc in docs:
        try:
            doc_ofc_newPresignedUrl = createPresignedUrl(bucket_name, str(doc.doc_official_file), expiration=3600)
            doc_address_newPresignedUrl = createPresignedUrl(bucket_name, str(doc.doc_address_file), expiration=3600)
            doc_selfie_newPresignedUrl = createPresignedUrl(bucket_name, str(doc.doc_selfie_file), expiration=3600)

            if doc_ofc_newPresignedUrl and doc_address_newPresignedUrl and doc_selfie_newPresignedUrl:
                b = models.CreatorsRequest.objects.get(doc_official_file=doc.doc_official_file,
                                                       doc_address_file=doc.doc_address_file,
                                                       doc_selfie_file=doc.doc_selfie_file)

                b.doc_official_url = doc_ofc_newPresignedUrl
                b.doc_address_url = doc_address_newPresignedUrl
                b.doc_selfie_url = doc_selfie_newPresignedUrl
                b.save()
        except Exception as e:
            print('Erro ao atualizar URL de post ID: ' + doc.id)
            print(e)
            pass
    return


def uploadFileToStripe(fileData):
    try:
        url = createPresignedUrl(settings.BUCKET_NAME, fileData, expiration=300)
        temp_download = requests.get(url)
        name_file_split = fileData.split('/')
        name_file_save = name_file_split[2]
        with open('spicyxapp/temp/temp_' + name_file_save, 'wb') as f:
            f.write(temp_download.content)

        with open('spicyxapp/temp/temp_' + name_file_save, 'rb') as fp:
            fileStripe = stripe.File.create(
                purpose='identity_document',
                file=fp
            )

            return {'stripe': fileStripe, 'temp_file': 'spicyxapp/temp/temp_' + name_file_save}
    except Exception as e:
        print('Error in uploading file to Stripe: ' + str(e))
        return None


def createProduct(name_month, price_month, description, profileUser, name_year, price_year):
    price_cents = int(price_month * 100)
    price_cents_year = int(price_year * 100)

    f = models.CreatorsRequest.objects.get(profile_creator=profileUser)
    stripe_file_front = uploadFileToStripe(str(f.doc_official_file))
    stripe_file_back = uploadFileToStripe(str(f.doc_official_file))

    try:
        product = stripe.Product.create(name=name_month,
                                        description=description,
                                        default_price_data={'currency': 'BRL',
                                                            'recurring': {'interval': 'month'},
                                                            'unit_amount': price_cents})
        product_year = stripe.Product.create(name=name_year,
                                             description=description,
                                             default_price_data={'currency': 'BRL',
                                                                 'recurring': {'interval': 'year'},
                                                                 'unit_amount': price_cents_year})
    except Exception as e:
        print('Error create product: ' + str(e))
        return None

    try:
        reqCreators_data = models.CreatorsRequest.objects.get(profile_creator=profileUser)
        fullname = reqCreators_data.full_name
        fullname_split = fullname.split(" ", 1)
        first_name = fullname_split[0]
        last_name = fullname_split[1]

        routing_number = str(reqCreators_data.bank) + '-' + str(reqCreators_data.bank_agency)

        dateNow = datetime.now()
        timestamp_now = time.mktime(dateNow.timetuple())

        if reqCreators_data.political_exposure == 'yes':
            political_exposure = 'existing'
        else:
            political_exposure = 'none'

        country_code = ''
        if reqCreators_data.country == 'BR':
            country_code = '+55'

        create_connectAccount = stripe.Account.create(type='custom',
                                                      country='BR',
                                                      email=profileUser.user.email,
                                                      default_currency='BRL',
                                                      capabilities={
                                                          'card_payments': {'requested': True},
                                                          'transfers': {'requested': True}},
                                                      business_type='individual',
                                                      business_profile={
                                                          'mcc': '5815',
                                                          'product_description': 'Produção e compartilhamento de '
                                                                                 'conteúdos exclusivos para '
                                                                                 'apoiadores por meio de '
                                                                                 'assinatura.',
                                                      },
                                                      tos_acceptance={
                                                          'date': int(timestamp_now),
                                                          'ip': str(reqCreators_data.user_ip),
                                                      },
                                                      individual={
                                                          'first_name': first_name,
                                                          'last_name': last_name,
                                                          'id_number': reqCreators_data.cpf,
                                                          'political_exposure': political_exposure,
                                                          'dob': {
                                                              'day': reqCreators_data.birth_day,
                                                              'month': reqCreators_data.birth_month,
                                                              'year': reqCreators_data.birth_year
                                                          },
                                                          'email': profileUser.user.email,
                                                          'phone': country_code + reqCreators_data.phone,
                                                          'address': {
                                                              'city': reqCreators_data.city,
                                                              'country': reqCreators_data.country,
                                                              'line1': reqCreators_data.full_address,
                                                              'line2': reqCreators_data.complement,
                                                              'postal_code': reqCreators_data.cep_address,
                                                              'state': reqCreators_data.state
                                                          },
                                                          'verification': {'document': {
                                                              'back': stripe_file_back['stripe'].id,
                                                              'front': stripe_file_front['stripe'].id
                                                          }},
                                                      },
                                                      external_account={
                                                          'object': 'bank_account',
                                                          'country': 'BR',
                                                          'currency': 'BRL',
                                                          'account_number': str(reqCreators_data.bank_account),
                                                          'routing_number': routing_number,
                                                      })
        save_Account_connect_stripe_id = models.Profile.objects.get(user=profileUser.user.id)
        save_Account_connect_stripe_id.account_connect_id = create_connectAccount.id
        save_Account_connect_stripe_id.save()

        reqCreators_data.doc_official_file_front_id = stripe_file_front['stripe'].id
        reqCreators_data.doc_official_file_back_id = stripe_file_back['stripe'].id
        reqCreators_data.save()

        saveProduct_monthBD = models.Product.objects.create(creator=profileUser,
                                                            product_id=product.id,
                                                            value=price_month,
                                                            active=False)
        saveProduct_yearBD = models.Product.objects.create(creator=profileUser,
                                                           product_id=product_year.id,
                                                           recurrence='year',
                                                           value=price_year,
                                                           active=False)
        try:
            os.remove(stripe_file_front['temp_file'])
        except Exception as e:
            print('Error in delete temp file doc : ' + str(e))
            return {'status': 'success'}
        return {'status': 'success'}

    except Exception as e:
        print('Error create connect account: ' + str(e))
        return None


def createRecurringSignature(productID, creator_userID, userID):
    try:
        response = stripe.Product.retrieve(productID)
    except Exception as e:
        print('Error in retrieving product: ' + str(e))
        return None

    customerID = ''
    try:
        customerExist = models.Profile.objects.get(user=userID)
        if customerExist.customer_id == '':
            first_name = customerExist.user.first_name
            last_name = customerExist.user.last_name
            full_name = first_name + ' ' + last_name
            newCustomer = stripe.Customer.create(name=full_name,
                                                 description=customerExist.nickname,
                                                 email=customerExist.user.email)
            saveCustomer = models.Profile.objects.get(user=userID)
            saveCustomer.customer_id = newCustomer.id
            saveCustomer.last_update_account = timezone.now()
            saveCustomer.save()
            customerID = newCustomer.id
        else:
            customerID = models.Profile.objects.get(user=userID).customer_id
    except Exception as e:
        print('Error in customer: ' + str(e))
        return None

    try:
        newSubscription = stripe.Subscription.create(
            customer=customerID,
            items=[{'price': response.default_price}],
            collection_method='send_invoice',
            days_until_due=3,
            description=response.description)
    except Exception as e:
        print('Error in creating new subscription: ' + str(e))
        return None

    try:
        sendInvoiceObj = stripe.Invoice.send_invoice(newSubscription.latest_invoice)
        user_creator = models.User.objects.get(id=creator_userID)
        saveInvoice = models.Invoice.objects.create(creator=user_creator,
                                                    fan=customerExist,
                                                    subscription_id=newSubscription.id,
                                                    invoice_id=newSubscription.latest_invoice,
                                                    invoice_url=sendInvoiceObj['hosted_invoice_url'],
                                                    value=sendInvoiceObj['total'] / 100,
                                                    status='pending')
        return sendInvoiceObj
    except Exception as e:
        print('Error in retrieve/save invoice object: ' + str(e))
        return None


def cancelSubscription(subscriptionID):
    try:
        response = stripe.Subscription.cancel(subscriptionID)
        if response:
            subFound = models.Subscriber.objects.get(subscription_id=subscriptionID, suspended=False)
            subFound.suspended = True
            subFound.save()

        return response
    except Exception as e:
        print('Error in cancel subscription: ' + str(e))
        pass


def saveWebhookBD(webhook_type, webhook_full):
    try:
        saveWebhookOBJ = models.Webhook.objects.create(
            webhook_type=str(webhook_type),
            webhook=str(webhook_full))
        return
    except Exception as e:
        print('Error in save webhook object: ' + str(e))
        pass


def createTransferConnect(amount, currency, destination, invoiceID, chargeID, profileCreator):
    # Movement between stripe connect accounts (commissions)
    transferInvoiceIdExist = models.TransferToConnectAccount.objects.filter(invoice_id=invoiceID, status='success')
    if transferInvoiceIdExist:
        return
    newTransfer = {}
    try:
        newTransfer = stripe.Transfer.create(
            amount=amount,
            currency=currency,
            destination=destination,
            source_transaction=chargeID
        )
    except Exception as e:
        print('Error in create new Transfer: ' + str(e))
        pass

    if newTransfer.id:
        transferID = newTransfer.id
        status = 'success'
    else:
        transferID = ''
        status = 'error'

    try:
        saveTransferBD = models.TransferToConnectAccount.objects.create(
            creator=profileCreator,
            account_connect_id=destination,
            invoice_id=invoiceID,
            value=amount / 100,
            status=status,
            transfer_stripe_id=transferID
        )
    except Exception as e:
        print('Error in save Transfer BD: ' + str(e))
        pass
    return newTransfer


# def createPayout():
#     # Withdrawal from Coonect account to bank
#     last_day_of_last_month = datetime.now().replace(day=1) - timedelta(days=1)
#     first_day_of_last_month = last_day_of_last_month.replace(day=1)
#     try:
#         profilesCreators = models.Profile.objects.filter(user_creator=True, suspended=False)
#         for creator in profilesCreators:
#             found_invoice = []
#             found_values = []
#             lastInvoices = models.Invoice.objects.filter(
#                 creator=creator.user,
#                 status='paid',
#                 updated_at__range=(first_day_of_last_month, last_day_of_last_month))
#             for invoice in lastInvoices:
#                 found_invoice.append(invoice.invoice_id)
#                 found_values.append(invoice.value)
#
#             # 50% to connect account
#             total_sum = sum(found_values) / 2
#             retrieve_amount_connect_account = stripe.Balance.retrieve(
#                 stripe_account=creator.account_connect_id
#             )
#
#             connect_actual_available_amount = retrieve_amount_connect_account.available[0].amount / 100
#             # connect_actual_pending_amount = retrieve_amount_connect_account.pending[0].amount / 100
#
#             if float(total_sum) > float(connect_actual_available_amount):
#                 error_withdraw = models.Payout.objects.create(
#                     creator=creator,
#                     account_connect_id=creator.account_connect_id,
#                     invoices_ids=found_invoice,
#                     total_amount_payout=total_sum,
#                     status='error',
#                     details='Valor de saque superior ao saldo disponível.'
#                 )
#             else:
#                 createPayout = stripe.Payout.create(
#                     amount=int(total_sum * 100),
#                     currency='BRL'
#                 )
#                 if createPayout.id:
#                     new_withdraw = models.Payout.objects.create(
#                         creator=creator,
#                         account_connect_id=creator.account_connect_id,
#                         invoices_ids=str(found_invoice),
#                         total_amount_payout=total_sum,
#                         status='success',
#                         payout_id=str(createPayout.id)
#                     )
#                     found_invoice.clear()
#                     found_values.clear()
#                     total_sum = 0
#
#     except Exception as e:
#         print('Error in payout: ' + str(e))
#         return


def createTransferReversal(transferID, amount_cents,
                           description, profileCreator,
                           accountConnectID, invoiceID):
    revTransfer = {}
    try:
        revTransfer = stripe.Transfer.create_reversal(
            transferID,
            amount=amount_cents,
            description=description
        )
        if revTransfer.id:
            saveRevTransfer = models.TransferToConnectAccount.objects.create(
                creator=profileCreator,
                account_connect_id=accountConnectID,
                invoice_id=invoiceID,
                value=amount_cents / 100,
                status='transfer reversal',
                transfer_stripe_id=revTransfer.id
            )
    except Exception as e:
        print('Error in save Reversal Transfer BD: ' + str(e))
        pass
    return revTransfer


def webhookReceived(webhook_full, webhookOBJ, webhook_type):
    saveWebhookBD(webhook_type, webhook_full)
    try:
        invoices = models.Invoice.objects.all()

        if webhook_type == 'customer.subscription.deleted':
            subData = models.Subscriber.objects.get(subscription_id=webhookOBJ.id)
            subData.suspended = True
            subData.save()
            for invoice in invoices:
                if (invoice.status == 'pending'
                        and invoice.subscription_id == webhookOBJ.id
                        and webhookOBJ.status == 'canceled'):
                    invoice.status = 'canceled'
                    invoice.save()

        elif webhook_type == 'customer.subscription.updated':
            if webhookOBJ.status == 'past_due':
                checkExistSubscription = models.Subscriber.objects.filter(subscription_id=webhookOBJ.id,
                                                                          suspended=False).exists()
                if checkExistSubscription:
                    sub = models.Subscriber.objects.get(subscription_id=webhookOBJ.id, suspended=False)
                    sub.suspended = True
                    sub.save()

        elif webhook_type == 'invoice.payment_succeeded':
            invoice = models.Invoice.objects.get(
                subscription_id=webhookOBJ.subscription,
                invoice_id=webhookOBJ.id)
            invoice.status = webhookOBJ.status
            invoice.charge_id = webhookOBJ.charge
            invoice.save()

            checkSubscriberExist = models.Subscriber.objects.filter(subscription_id=webhookOBJ.subscription,
                                                                    suspended=False).exists()
            if not checkSubscriberExist:
                createSubscriber = models.Subscriber.objects.create(
                    creator=invoice.creator,
                    subscriber=invoice.fan,
                    subscription_id=invoice.subscription_id)

            # transfer 50%
            amount = int(webhookOBJ.amount_paid / 2)
            creator = invoice.creator
            createTransfer = createTransferConnect(
                amount,
                'BRL',
                str(creator.profile.account_connect_id),
                str(webhookOBJ.id),
                str(webhookOBJ.charge),
                creator.profile)

        elif webhook_type == 'product.created':
            product = models.Product.objects.get(product_id=webhookOBJ.id)
            product.active = True
            product.save()

        elif webhook_type == 'charge.refunded':
            invoice = models.Invoice.objects.get(invoice_id=webhookOBJ.invoice)
            invoice.status = 'refunded'
            invoice.save()
            cancel_Subscription = cancelSubscription(invoice.subscription_id)
            accountConnectID = invoice.creator.profile.account_connect_id

            checkRevTransferExist = models.TransferToConnectAccount.objects.filter(
                account_connect_id=accountConnectID,
                invoice_id=invoice.invoice_id, status='transfer reversal').exists()
            if not checkRevTransferExist:
                transferData = models.TransferToConnectAccount.objects.get(
                    account_connect_id=accountConnectID,
                    invoice_id=invoice.invoice_id)
                trDesc = 'Requested refund on platform.'
                rev = createTransferReversal(transferData.transfer_stripe_id, int(transferData.value * 100),
                                             trDesc, invoice.creator.profile, accountConnectID, invoice.invoice_id)

        elif webhook_type == 'invoice.created':
            checkInvoiceExist = models.Invoice.objects.filter(invoice_id=str(webhookOBJ.id)).exists()
            if not checkInvoiceExist:
                if webhookOBJ.status == 'draft':
                    invoiceStatus = 'pending'
                else:
                    invoiceStatus = webhookOBJ.status

                valueInvoice = float(webhookOBJ.amount_remaining / 100)
                invoiceID = str(webhookOBJ.id)
                customerID = str(webhookOBJ.customer)
                subscriptionID = str(webhookOBJ.subscription)
                subDATA = models.Subscriber.objects.get(subscription_id=subscriptionID)
                retrieveInvoice = stripe.Invoice.finalize_invoice(invoiceID)
                if retrieveInvoice:
                    saveNewInvoice = models.Invoice.objects.create(
                        creator=subDATA.creator,
                        fan=subDATA.subscriber,
                        subscription_id=subscriptionID,
                        invoice_id=invoiceID,
                        invoice_url=str(retrieveInvoice.hosted_invoice_url),
                        value=valueInvoice,
                        status=invoiceStatus
                    )

        elif webhook_type == 'charge.dispute.created':
            disputeExist = models.DisputeChargeback.objects.filter(dispute_id=webhookOBJ.id,
                                                                   charge_id=webhookOBJ.charge).exists()
            if not disputeExist:
                saveDisputeBD = models.DisputeChargeback.objects.create(
                    dispute_id=webhookOBJ.id,
                    charge_id=webhookOBJ.charge,
                    value=webhookOBJ.amount / 100,
                    reason=webhookOBJ.reason,
                    description=webhookOBJ.balance_transactions[0].description,
                    status=webhookOBJ.status
                )
            else:
                checkDisputeStatus = models.DisputeChargeback.objects.get(dispute_id=webhookOBJ.id,
                                                                          charge_id=webhookOBJ.charge)
                if checkDisputeStatus.status == 'needs_response':
                    pass
                elif checkDisputeStatus.status == 'accepted':
                    return

            invoiceData = {}
            try:
                invoiceData = models.Invoice.objects.get(charge_id=webhookOBJ.charge)
                if invoiceData.invoice_id:
                    invoiceData.status = 'refunded'
                    invoiceData.save()
            except Exception as e:
                print('Error in query invoice or chargeID not exist. ' + str(e))
                return

            transferDataExist = models.TransferToConnectAccount.objects.filter(invoice_id=invoiceData.invoice_id,
                                                                               status='transfer reversal').exists()
            if not transferDataExist:
                transferData = models.TransferToConnectAccount.objects.get(invoice_id=invoiceData.invoice_id)
                revTransfer = createTransferReversal(
                    transferData.transfer_stripe_id,
                    int(transferData.value*100),
                    'Received dispute on platform.',
                    invoiceData.creator.profile,
                    transferData.account_connect_id,
                    invoiceData.invoice_id)
                try:
                    acceptDispute = stripe.Dispute.close(webhookOBJ.id)
                    if acceptDispute.id:
                        updateDisputeBD = models.DisputeChargeback.objects.get(dispute_id=webhookOBJ.id)
                        updateDisputeBD.creator = invoiceData.creator
                        updateDisputeBD.status = 'accepted'
                        updateDisputeBD.save()
                except Exception as e:
                    print('Error in accept dispute: ' + str(e))
                    pass
                
                try:
                    cancelSub = cancelSubscription(invoiceData.subscription_id)
                except Exception as e:
                    print('Error in cancel subscription in dispute: ' + str(e))
                    pass

    except Exception as e:
        print('Error in webhookReceived: ' + str(e))
        pass
