import 'dart:convert';
import 'package:campoundnew/model/PartyBooking.dart';
import 'package:dio/dio.dart';

class PartyApi {
  final Dio _dio = Dio();

  // Constructor
  PartyApi() {
    _dio.options.headers = {
      'Content-Type': 'application/json',
    };
  }

  // إعداد التوكن في كل طلب
  Future<void> setToken(String token) async {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  // دالة لجلب بيانات الحفلات من API
  Future<List<PartyBooking>> fetchBookings(String token) async {
    print("Token: $token");
    try {
      final response = await _dio.get(
        'http://10.0.2.2:8000/api/admin/party-bookings', // تعديل المسار إلى party-bookings
        options: Options(headers: {
          'Authorization': 'Bearer $token',
        }),
      );

      if (response.statusCode == 200) {
        List<dynamic> data = response.data;
        return data.map((json) => PartyBooking.fromJson(json)).toList();
      } else {
        print("Response: ${response.data}"); // طباعة الاستجابة
        throw Exception('Failed to load bookings');
      }
    } catch (e) {
      print("Error: $e"); // طباعة تفاصيل الخطأ
      throw Exception('Failed to load bookings: $e');
    }
  }

  // دالة لتحديث حجز حفلة
  Future<void> updateBooking(String token, int id, PartyBooking booking) async {
    try {
      print("Token: $token");

      await setToken(token); // إعداد التوكن
      final response = await _dio.put(
        'http://10.0.2.2:8000/api/admin/party-booking/$id', // تعديل المسار إلى party-booking
        data: json.encode({
          'party_date': booking.partyDate, // تعديل الحقول إلى بيانات الحفلات
          'reason': booking.reason,
          'guests_count': booking.guestsCount,
          'start_time': booking.startTime,
          'end_time': booking.endTime,
          'email': booking.email,
        }),
      );
      if (response.statusCode == 200) {
        print("Booking updated successfully");
      } else {
        print("Failed to update booking");
      }
    } catch (e) {
      print("Error updating booking: $e");
    }
  }

  // دالة لحذف حجز حفلة
  Future<void> deleteBooking(String token, int id) async {
    try {
      await setToken(token); // إعداد التوكن
      final response = await _dio.delete(
          'http://10.0.2.2:8000/api/admin/party-booking/$id'); // تعديل المسار إلى party-booking
      if (response.statusCode == 200) {
        print("Booking deleted successfully");
      } else {
        print("Failed to delete booking");
      }
    } catch (e) {
      print("Error deleting booking: $e");
    }
  }
}
