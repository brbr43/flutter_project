import 'package:campoundnew/model/complaintBooking.dart';
import 'package:dio/dio.dart';

class Complaintapi {
  final Dio _dio = Dio();

  // Constructor
  Complaintapi() {
    _dio.options.headers = {
      'Content-Type': 'application/json',
    };
  }

  // إعداد التوكن في كل طلب
  Future<void> setToken(String token) async {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  Future<List<Complaintbooking>> fetchComplaints(String token) async {
    print("Token: $token");
    try {
      final response = await _dio.get(
        'http://10.0.2.2:8000/api/admin/complaints', // تعديل المسار إلى party-bookings
        options: Options(headers: {
          'Authorization': 'Bearer $token',
        }),
      );

      if (response.statusCode == 200) {
        List<dynamic> data = response.data;
        return data.map((json) => Complaintbooking.fromJson(json)).toList();
      } else {
        print("Response: ${response.data}"); // طباعة الاستجابة
        throw Exception('Failed to load bookings');
      }
    } catch (e) {
      print("Error: $e"); // طباعة تفاصيل الخطأ
      throw Exception('Failed to load bookings: $e');
    }
  }

  // دالة لحذف حجز حفلة
  Future<void> deleteComplaint(String token, int id) async {
    try {
      await setToken(token); // إعداد التوكن
      final response = await _dio.delete(
          'http://10.0.2.2:8000/api/admin/complaints/$id'); // تعديل المسار إلى
      if (response.statusCode == 200) {
        print("complaint deleted successfully");
      } else {
        print("Failed to delete complaint");
      }
    } catch (e) {
      print("Error deleting complaint: $e");
    }
  }
}
