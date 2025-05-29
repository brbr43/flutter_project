import 'package:dio/dio.dart';

class Yogabooking {
  final Dio _dio = Dio();

  Future<void> addBooking(String reservationDate, String startTime,
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
        'http://10.0.2.2:8000/api/gym-booking',
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
      } else {
        print('Failed to add booking.');
        print('Response data: ${response.data}');
      }
    } catch (e) {
      print('Error: $e');
    }
  }
}
