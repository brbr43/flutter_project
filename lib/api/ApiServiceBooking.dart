import 'dart:convert';
import 'package:campoundnew/model/BookingData.dart';
import 'package:dio/dio.dart';

class ApiServiceBooking {
  final Dio _dio = Dio(); // يجب إنشاء مثيل من Dio
  final String baseUrl = "http://10.0.2.2:8000/api/bookings";

  Future<BookingData?> fetchBookings(String token) async {
    try {
      if (token.isEmpty) {
        print("❌ خطأ: التوكن غير متوفر!");
        return null;
      }

      print("✅ التوكن المستخدم: $token");

      Response response = await _dio.get(
        baseUrl,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Accept': 'application/json',
          },
        ),
      );

      print("📥 استجابة الـ API: ${response.data}");

      if (response.statusCode == 200) {
        // تم تصحيح التحويل إلى BookingData باستخدام response.data مباشرة
        return BookingData.fromJson(response.data['data']);
      } else {
        print("❌ فشل في تحميل البيانات، كود الحالة: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("❌ خطأ أثناء تحميل البيانات: $e");
      return null;
    }
  }

  Future<bool> updateBooking(String token, String bookingType, int id,
      Map<String, dynamic> updatedData) async {
    try {
      if (token.isEmpty) {
        print("❌ خطأ: التوكن غير متوفر!");
        return false;
      }

      print("✅ التوكن المستخدم: $token");

      String url = "http://10.0.2.2:8000/api/booking/$id";
      print(url);
      Response response = await _dio.put(
        url,
        data: updatedData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Accept': 'application/json',
          },
        ),
      );

      print("📥 استجابة الـ API: ${response.data}");
      print("📥 كود الحالة: ${response.statusCode}");

      if (response.statusCode == 200) {
        return true; // تم التعديل بنجاح
      } else {
        print("❌ فشل في تعديل الحجز، كود الحالة: ${response.statusCode}");
        return false;
      }
    } catch (e) {
      print("❌ خطأ أثناء تعديل الحجز: $e");
      return false;
    }
  }

  Future<bool> deleteBooking(String token, String bookingType, int id) async {
    try {
      if (token.isEmpty) {
        print("❌ خطأ: التوكن غير متوفر!");
        return false;
      }

      print("✅ التوكن المستخدم: $token");

      // بناء الـ URL مع تحديد نوع الحجز وID الحجز
      String url = "http://10.0.2.2:8000/api/booking/$bookingType/$id";
      print("🔗 URL الحذف: $url");

      Response response = await _dio.delete(
        url,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
            'Accept': 'application/json',
          },
        ),
      );

      print("📥 استجابة الـ API: ${response.data}");

      if (response.statusCode == 200) {
        return true; // تم الحذف بنجاح
      } else {
        print("❌ فشل في حذف الحجز، كود الحالة: ${response.statusCode}");
        print("📄 تفاصيل الاستجابة: ${response.data}");
        return false;
      }
    } catch (e) {
      if (e is DioException) {
        print("❌ استثناء Dio: ${e.message}");
        // هنا يمكنك التعامل مع الاستثناءات المحددة مثل 400، 404، 500
        if (e.response != null) {
          print("🔴 الاستجابة: ${e.response?.data}");
        }
      } else {
        print("❌ خطأ غير معروف أثناء حذف الحجز: $e");
      }
      return false;
    }
  }
}
