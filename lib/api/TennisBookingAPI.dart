import 'package:dio/dio.dart';

class TennisBookingAPI {
  final Dio _dio = Dio();

  Future<bool> addBooking(String reservationDate, String startTime,
      String endTime, String token) async {
    // إزالة AM/PM من الأوقات
    startTime = startTime.replaceAll(RegExp(r' AM| PM'), '');
    endTime = endTime.replaceAll(RegExp(r' AM| PM'), '');

    print("start time:$startTime");
    print("endTime:$endTime");
    print("reservationDate:$reservationDate");

    try {
      print("Token: $token");

      final response = await _dio.post(
        'http://10.0.2.2:8000/api/tennis-booking',
        data: {
          "reservation_date": reservationDate,
          "start_time": startTime,
          "end_time": endTime,
        },
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
      );

      if (response.statusCode == 201) {
        print('Booking added successfully!');
        return true; // ✅ نجاح الحجز
      } else {
        print('Failed to add booking.');
        print('Response data: ${response.data}');
        return false; // ❌ فشل الحجز
      }
    } catch (e) {
      print('Error: $e');
      return false; // ⚠️ حدث خطأ
    }
  }
}
