import 'dart:convert';
import 'package:http/http.dart' as http;

Future<void> sendNotification(String title, String content) async {
  var headers = {
    'Content-Type': 'application/json; charset=UTF-8',
    'Authorization':
        'Basic YjVkZTlkZTAtOWVjMC00N2E2LWI5YzYtMjQ3OGRhODliY2I4', // REST API Key الخاص بك
  };

  var request = {
    'app_id': '4e73f170-afab-4415-be7c-50e3dc09b086', // App ID الخاص بك
    'included_segments': ['All'],
    'headings': {'en': title},
    'contents': {'en': content},
  };

  try {
    var response = await http.post(
      Uri.parse('https://onesignal.com/api/v1/notifications'),
      headers: headers,
      body: jsonEncode(request),
    );

    if (response.statusCode == 200) {
      print('✅ Notification sent successfully!');
    } else {
      print('❌ Failed to send notification.');
      print('Response Body: ${response.body}');
      print('Status Code: ${response.statusCode}');
    }
  } catch (e) {
    // معالجة الأخطاء غير المتوقعة
    print('❌ Error occurred while sending notification: $e');
  }
}
