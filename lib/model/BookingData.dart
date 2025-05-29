// booking_model.dart

class TennisBooking {
  final int id;
  final String reservationDate;
  final String startTime;
  final String endTime;

  TennisBooking(
      {required this.id,
      required this.reservationDate,
      required this.startTime,
      required this.endTime});

  factory TennisBooking.fromJson(Map<String, dynamic> json) {
    return TennisBooking(
      id: json['id'],
      reservationDate: json['reservation_date'],
      startTime: json['start_time'],
      endTime: json['end_time'],
    );
  }
}

class GymBooking {
  final int id;
  final String reservationDate;
  final String startTime;
  final String endTime;

  GymBooking(
      {required this.id,
      required this.reservationDate,
      required this.startTime,
      required this.endTime});

  factory GymBooking.fromJson(Map<String, dynamic> json) {
    return GymBooking(
      id: json['id'],
      reservationDate: json['reservation_date'],
      startTime: json['start_time'],
      endTime: json['end_time'],
    );
  }
}

class PartyBooking {
  final int id;
  final String partyDate;
  final String reason;
  final int guestsCount;
  final String startTime;
  final String endTime;

  PartyBooking(
      {required this.id,
      required this.partyDate,
      required this.reason,
      required this.guestsCount,
      required this.startTime,
      required this.endTime});

  factory PartyBooking.fromJson(Map<String, dynamic> json) {
    return PartyBooking(
      id: json['id'],
      partyDate: json['party_date'],
      reason: json['reason'],
      guestsCount: json['guests_count'],
      startTime: json['start_time'],
      endTime: json['end_time'],
    );
  }
}

class BookingData {
  final List<TennisBooking> tennisBookings;
  final List<GymBooking> gymBookings;
  final List<PartyBooking> partyBookings;

  BookingData(
      {required this.tennisBookings,
      required this.gymBookings,
      required this.partyBookings});

  factory BookingData.fromJson(Map<String, dynamic> json) {
    var tennisList = (json['tennis_bookings'] as List)
        .map((e) => TennisBooking.fromJson(e))
        .toList();
    var gymList = (json['gym_bookings'] as List)
        .map((e) => GymBooking.fromJson(e))
        .toList();
    var partyList = (json['party_bookings'] as List)
        .map((e) => PartyBooking.fromJson(e))
        .toList();

    return BookingData(
      tennisBookings: tennisList,
      gymBookings: gymList,
      partyBookings: partyList,
    );
  }
}
