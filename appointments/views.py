from datetime import date, datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import authentication_classes, permission_classes

from user.views import ProfessionalsByIdView
from .models import AppointmentsModel
from .serializers import AllAppointmentsSerializer, AppPatientSerializer, AppProfessonalSerializer, AppointmentsSerializer, AppointmentsToUpdateSerializer
from .permissions import AppointmentPermission
from user.models import Patient, Professional, User
from user.serializers import PatientSerializer, ProfessionalSerializer, NewPatientSerializer

import ipdb


class SpecificPatientView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, cpf=''):
        try:
            patient = Patient.objects.get(cpf=cpf)

            if patient:
                appointment = AppointmentsModel.objects.filter(patient=patient)
                serializer = AppointmentsSerializer(appointment, many=True)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except Patient.DoesNotExist:
            return Response(
                {"message": "Patient does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class SpecificProfessionalView(APIView):
    print('***')
    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, council_number=''):
        try:
            professional = Professional.objects.get(council_number=council_number)

            if professional:
                appointment = AppointmentsModel.objects.filter(professional=professional)

                serializer = AppointmentsSerializer(appointment, many=True)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except Professional.DoesNotExist:
            return Response(
                {"message": "Professional not registered"}, status=status.HTTP_404_NOT_FOUND,
            )


class SpecificAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, appointment_id=''):
        try:
            appointment = AppointmentsModel.objects.get(uuid=appointment_id)

            if appointment:

                serializer = AppointmentsSerializer(appointment)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except AppointmentsModel.DoesNotExist:
            return Response(
                {"message": "Appointment not registered"}, status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, appointment_id=''):
        try:
            appointment = AppointmentsModel.objects.get(uuid=appointment_id)

            if appointment:
                serialized = AppointmentsToUpdateSerializer(data=request.data, partial=True)

                if serialized.is_valid():
                    data = {**serialized.validated_data}

                    for key, value in data.items():
                        appointment.__dict__[key] = value

                    appointment.save()

                    updated_appointment = AppointmentsModel.objects.get(uuid=appointment_id)
                    serialized = AppointmentsSerializer(updated_appointment)

                    return Response(serialized.data, status=status.HTTP_200_OK)

        except AppointmentsModel.DoesNotExist:
            return Response({'message': 'Appointment does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, appointment_id=''):
        try:
            appointment = AppointmentsModel.objects.get(uuid=appointment_id)

            if appointment:

                appointment.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

        except AppointmentsModel.DoesNotExist:
            return Response({'message': 'Appointment does not exist'}, status=status.HTTP_404_NOT_FOUND)


class TomorrowAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, council_number=''):
        try:
            professional = Professional.objects.get(council_number=council_number)

            if professional:
                now = datetime.now()
                tomorrow = datetime.now().date() + timedelta(days=1)
                end_tomorrow = tomorrow + timedelta(days=1)
                appointments_for_tomorrow = AppointmentsModel.objects.filter(date__range=[tomorrow, end_tomorrow])

                # ipdb.set_trace()
                if appointments_for_tomorrow:
                    for unfinished in appointments_for_tomorrow:
                        serializer = AppointmentsSerializer(unfinished)

                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response({"message": "No appointments for tomorrow!"}, status=status.HTTP_200_OK)

        except Professional.DoesNotExist:
            return Response({"message": "Professional not registered"}, status=status.HTTP_404_NOT_FOUND)

        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class NotFinishedAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request):
        try:

            not_finished_appointment = AppointmentsModel.objects.filter(finished=False)

            for unfinished in not_finished_appointment:
                serializer = AppointmentsSerializer(unfinished)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                {"message": "Professional not registered"},
                status=status.HTTP_404_NOT_FOUND,
            )


class CreateAppointment(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def post(self, request):

        professional = Professional.objects.get(council_number=request.data['council_number'])

        patient = Patient.objects.get(cpf=request.data['cpf']) 

        data=request.data

        prof = ProfessionalSerializer(professional)
        # pat = NewPatientSerializer(patient)
        pat = PatientSerializer(patient)

        data['professional'] = prof.data["council_number"]
        data['patient'] = pat.data["cpf"]

        serializer = AppointmentsSerializer(
            data=data
        )
        
        # print(serializer.validated_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.validated_data['professional'] = professional
        serializer.validated_data['patient'] = patient
        appointment = AppointmentsModel.objects.create(**serializer.validated_data)
        serializer = AppointmentsSerializer(appointment)

        return Response(serializer.data, status=status.HTTP_201_CREATED)