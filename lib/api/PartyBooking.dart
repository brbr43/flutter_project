import 'package:dio/dio.dart';

class Partybooking {
  final Dio _dio = Dio();

  Future<bool> addBooking(String reservationDate, String reason,
      int guestsCount, String startTime, String endTime, String token) async {
    // إزالة AM/PM من الأوقات
    startTime = startTime.replaceAll(RegExp(r' AM| PM'), '');
    endTime = endTime.replaceAll(RegExp(r' AM| PM'), '');

    print("📅 Reservation Date: $reservationDate");
    print("⏰ Start Time: $startTime");
    print("⏰ End Time: $endTime");
    print("🎉 Reason: $reason");
    print("👥 Guests Count: $guestsCount");
    print("🔑 Token: $token");

    try {
      final response = await _dio.post(
        'http://10.0.2.2:8000/api/party-booking',
        data: {
          "party_date": reservationDate,
          "reason": reason,
          "guests_count": guestsCount,
          "start_time": startTime,
          "end_time": endTime,
        },
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
      );

      print("🔄 Response Status Code: ${response.statusCode}");
      print("📥 Response Data: ${response.data}");

      if (response.statusCode == 201) {
        print('✅ Booking added successfully!');
        return true;
      } else {
        print('❌ Failed to add booking.');
        return false;
      }
    } catch (e) {
      print('⚠️ Error: $e');
      return false;
    }
  }
}
