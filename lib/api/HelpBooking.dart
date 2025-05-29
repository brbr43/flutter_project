import 'package:dio/dio.dart';

class Helpbooking {
  final Dio _dio = Dio();

  Future<void> addBooking(String message, String token) async {
    // إزالة AM/PM من الأوقات

    try {
      print("Token: $token");

      final response = await _dio.post(
        'http://10.0.2.2:8000/api/complaints',
        data: {
          "message": message,
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
