import requests
from rest_framework import views
from rest_framework.response import Response

class PurchaseProductView(views.APIView):

    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        #TODO 1. Verificar disponibilidade do estoque no Inventory Service
        try:
            inventory_check_response = requests.get(f'http://localhost:8002/api/inventory/{product_id}/')
            inventory_check_response.raise_for_status()

            if inventory_check_response.status_code != 200:
                return Response({'error': 'Failed to check inventory'}, status=400)

            available_quantity = inventory_check_response.json().get('available_quantity')

            if available_quantity < quantity:
                return Response({'error': 'Insufficient inventory'}, status=400)
        except requests.RequestException:
            return Response({'error': 'Failed to check inventory'}, status=500)

        # 2. Criar o pedido no Product Service
        try:
            order_response = requests.post('http://localhost:8001/api/orders/', json={
                'product_id': product_id,
                'quantity': quantity
            })
            order_response.raise_for_status()

            if order_response.status_code != 200:
                return Response({'error': 'Failed to create order'}, status=400)

        except requests.RequestException:
            return Response({'error': 'Failed to create order'}, status=500)

        order_id = order_response.json().get('order_id')

        # 3. Reservar o inventário no Inventory Service
        try:
            inventory_reserve_response = requests.post('http://localhost:8002/api/inventory/reserve/', json={
                'product_id': product_id,
                'quantity': quantity
            })
            inventory_reserve_response.raise_for_status()

            if inventory_reserve_response.status_code != 200:
                return Response({'error': 'Failed to reserve inventory'}, status=400)
            
        except requests.RequestException:
            return Response({'error': 'Failed to reserve inventory'}, status=500)

        #TODO 4. Processar o pagamento no Payment Service

        try:
            payment_response = requests.post('http://localhost:8003/api/payments/', json={
                'order_id': order_id,
                'amount': 10.00
            })
            payment_response.raise_for_status()

            if payment_response.status_code != 200:
                return Response({'error': 'Failed to process payment'}, status=400)
        except requests.RequestException:
            self.payment_error_handler(product_id, available_quantity)
            return Response({'error': 'Failed to process payment'}, status=500)
    

        return Response({'status': 'Purchase Completed'})
    
    def payment_error_handler(self, product, quantity):
        try:
            inventory_return_response = requests.post('http://localhost:8002/api/inventory/return/', json={
                'product_id': product,
                'quantity': quantity
            })
            inventory_return_response.raise_for_status()
        except requests.RequestException:
            return Response({'error': 'Failed to return inventory'}, status=500)

