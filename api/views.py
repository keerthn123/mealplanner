import os
import json
from django.db import connection, IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

import google.generativeai as genai
from .serializers import UserSerializer
from django.views.decorators.csrf import csrf_exempt

genai.configure(api_key="AIzaSyCtobsZAKGo1xHLpAFIptHnpSTPOSr7weU")
model = genai.GenerativeModel("gemini-1.5-flash")

@api_view(['POST'])
@csrf_exempt 
def user_login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({'detail': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = get_object_or_404(User, email=email)
        if user.check_password(password):
            token, _ = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user)
            return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@csrf_exempt 
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_logout(request):
    try:
        token_key = request.headers.get('Authorization').split(' ')[1]
        token = Token.objects.get(key=token_key)
        token.delete()
        return Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@csrf_exempt 
def user_register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(request.data.get('password'))
        user.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt 
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def getMeals(request):
    try:
        mealType = request.data.get('mealType')
        targetCals = request.data.get("targetCals")
        system_message = (
                'You are a physical health doctor who suggests meals and workout plan to the clients. when given his meal type like lunch, breakfast or dinner, based on his wanted calories. suggest him some good meals/food to eat'
                f'The meal type is {mealType}. '
                f'The required calories by the user are: {targetCals}. '
                'Send the response in the following JSON format { [ {name: "meal-item-1", quantity: "300 grams", imageUrl: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSK6ghC4OB1yk7uqJoEupPCdoFFfYecE5J_UQ&s" , benifits: "This meal contains good number of fats and anti-oxidants and many other health benifits" }, {name: meal-item-2, quantity: 500 grams, imageUrl:"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSK6ghC4OB1yk7uqJoEupPCdoFFfYecE5J_UQ&s",  benifits: "This meal contains good number of fats and anti-oxidants and many other health benifits" } ] }.'
                'please do not generate any extra characters other than the json. The response should be a proper JSON string'
            )
        response = model.generate_content(system_message)
        generated_text = clean_json_string(response.text)
        # data = json.loads(generated_text)    
        return Response(generated_text, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@csrf_exempt 
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def getWorkout(request):
    try:
        goal = request.data.get('mealType')
        level = request.data.get("targetCals")
        system_message = (
                'You are a physical health doctor who suggests meals and workout plan to the clients. given his fitness goals you have to suggest him good exercises like pushup, pullups, bench press and many more..'
                f'The fitness goal is {goal}. '
                f'The intesity level of the workout that the user is redy for is: {level}. '
                'Send the response in the following JSON format { [ {name: "Exercise-1(example: push-ups)", sets: "number of sets(example:5)", reps: "number of repetitions (example:20)", benifits: "this exercise is good for your arms and shoulders which increases strength and stabitlity" }, {name: "Exercise-2(example: pull-ups)", sets: "number of sets(example:5)", reps: "number of repetitions (example:20)", benifits: "this exercise is good for your arms and shoulders which increases strength and stabitlity" } ] }.'
                'please do not generate any extra characters other than the json. The response should be a proper JSON string'
            )
        response = model.generate_content(system_message)
        generated_text = clean_json_string(response.text)
        # data = json.loads(generated_text)    
        return Response(generated_text, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['POST'])
@csrf_exempt 
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def getCals(request):
    try:
        meal = request.data.get('meal')
        quantity = request.data.get("quantity")
        system_message = (
                'You are a physical health doctor who suggests meals and workout plan to the clients. when given his meal details like what food he consumed and quantity he consumed, You have to calculate the amount of calories that he consumed and suggest him if it was the right choice and let hime know what he has to do next, like walk more today.'
                f'The meal he had is {meal}. '
                f'The quantity of the meal he had is: {quantity}. '
                'Send the response in the following JSON format { [ {caloryCount: "2000", contains: "The given food contains proteins, fats and fibres and <please include all the other nutrients, anti-oxidants, or any others that in the food>, suggestions: "The food you consumed is a good choice, it is better to workout with weights to make most out of your protein intake", imageUrl: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSK6ghC4OB1yk7uqJoEupPCdoFFfYecE5J_UQ&s" } ] }.'
                'please do not generate any extra characters other than the json. The response should be a proper JSON string'
            )
        response = model.generate_content(system_message)
        generated_text = clean_json_string(response.text)
        # data = json.loads(generated_text)    
        return Response(generated_text, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
import re

def clean_json_string(json_string):
    cleaned_string = re.sub(r'^```json\n|\n```$', '', json_string)
    
    cleaned_string = re.sub(r'\n\s*', '', cleaned_string)
    try:
        parsed_json = json.loads(cleaned_string)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None
class GetMeals(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        table_name = request.data.get('table_name')
        prompt = request.data.get('prompt')

        if not table_name or not prompt:
            return Response({'error': 'Table name and prompt are required'}, status=400)

        try:
            

            # Get table columns dynamically
            csv_file = UserCSVFile.objects.get(table_name=table_name, user=request.user)
            columns_str = ', '.join([col['name'] for col in csv_file.columns])

            system_message = (
                'You are a Data Scientist Who writes SQL queries for PostgreSQL. when a natural language request is given you will understand the requirement and write the Postgres SQL query'
                f'The table name is {table_name}. '
                f'The columns of this table are: {columns_str}. '
                'Remember, while writing a query, put the colum names in "". Example: SELECT "PRICE" FROM TABLE;. '
                'The query should be a single line query. Please do not use new line characters'
                'Send the response in the following JSON format Recipe = { query: <Query>}.'
                'Return Recipe'
                'Please dont start the response with `json` word'
                'Here is the Natural language prompt: '
            )

            response = model.generate_content(
                system_message+prompt
            )

            generated_text = response.text.strip('`').replace('json\n', '').replace('\n```', '')
            data = json.loads(generated_text)
            sql_query = data["query"]

            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return Response({'custom_query_results': results})

        except Exception as e:
            return Response({'error': str(e)}, status=500)
        

class DynamicTableQueryView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle aggregate and search queries for user's uploaded CSV tables
        """
        query_params = request.query_params
        
        if not query_params:
            return Response({'error': 'No query parameters provided'}, status=400)

        table_name = query_params.get('table_name')
        field = query_params.get('field')
        value = query_params.get('value')
        operator = query_params.get('operator', '=')

        if not table_name or not field:
            return Response({'error': 'Table name and field are required'}, status=400)

        try:
            # Verify the table belongs to the user
            csv_file = UserCSVFile.objects.get(table_name=table_name, user=request.user)
            
            # Validate field exists in the table's columns
            field_exists = any(col['name'] == field for col in csv_file.columns)
            if not field_exists:
                return Response({'error': f'Invalid field: {field}'}, status=400)

            # Determine field type
            field_type = next((col['type'] for col in csv_file.columns if col['name'] == field), None)

            # Perform search
            search_results = self._get_search_results(table_name, field, operator, value) if value is not None else None

            # Perform aggregate results
            aggregate_results = self._get_aggregate_results(table_name, field, field_type)

            # Perform constrained aggregate results
            constrained_aggregate_results = None
            if field_type in ['int64', 'float64'] and value is not None:
                constrained_aggregate_results = self._get_constrained_aggregate_results(
                    table_name, field, operator, value
                )

            return Response({
                'search_results': search_results,
                'aggregate_results': aggregate_results,
                'constrained_aggregate_results': constrained_aggregate_results
            })

        except UserCSVFile.DoesNotExist:
            return Response({'error': 'Table not found or unauthorized'}, status=403)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

