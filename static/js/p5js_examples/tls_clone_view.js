
class TLSMainPage {
    constructor(width, height) {
        this.width = width;
        this.height = height;

        let minTimelineHeight = 100;
        let timelineHeight = this.height * 0.2;
        if (timelineHeight < minTimelineHeight) {
            timelineHeight = minTimelineHeight;
        }
        this._timeline = new TimeLine(0, this.height - timelineHeight, this.width, timelineHeight);
        this._actionButtons = [new Button(), new Button(), new Button()];
        this._events = [];
    }

    AddEvent(event) {
        //make sure an event with the same ID doesnt already exists
        this._events.forEach(e => {
            if (e["ItemId"] == event["ItemId"]) {
                return;
            }
        });
        // if we got here, then there is no ItemId conflict
        this._events.push(event);
    }

    DeleteEvent(eventID) {
        let indexToRemove = [];

        this._events.forEach(event => {
            if (event["ItemId"] == eventID) {
                let index = this._events.indexOf(event);
                indexToRemove.push(index);
            }
        });

        indexToRemove.forEach(index => {
            this._events = this._events.splice(index, 1);
        });
    }

    ClearEvents() {
        this._events = [];
    }

    TextWithShadow(userText, xCenter, yTop, color, size) {
        let offset = 1;

        noStroke();

        textSize(size);
        textAlign(CENTER, TOP);

        // draw another text slightly shifted and dark
        fill("grey");
        text(userText, xCenter + offset, yTop + offset);

        // draw the top layer
        fill(color);
        text(userText, xCenter, yTop);
    }

    Draw() {
        background("white");
        let available = true;
        let allLeftPadding = 10;
        /////////////////////////////////////////////////////

        // draw the timeline
        this._timeline.Draw();

        // draw the current time
        let currentTimeTopPadding = 20;

        let minCurrentTimeTextSize = 14;
        let currentTimeTextSize = this.height * 0.035;
        if (currentTimeTextSize < minCurrentTimeTextSize) {
            currentTimeTextSize = minCurrentTimeTextSize;
        }

        let currentTimeY =
            this.height - this._timeline.height - currentTimeTextSize - currentTimeTopPadding;
        let currentTimeX = allLeftPadding;
        textSize(currentTimeTextSize);
        fill("black");
        text("<currentTime>", currentTimeX, currentTimeY);

        // draw the availablility indicator (aka a rect)
        let availabilityTopPadding = 10;
        let availabilityIndicatorY = availabilityTopPadding;
        let minAvailabilityIndicatorWidth = 50;
        let availablilityIndicatorWidth = this.width * 0.15;
        let avilabilityIndicatorHeight =
            currentTimeY - availabilityTopPadding - currentTimeTopPadding;

        if (availablilityIndicatorWidth < minAvailabilityIndicatorWidth) {
            availablilityIndicatorWidth = minAvailabilityIndicatorWidth;
        }
        let availabilityIndicatorColor = "blue";
        if (available) {
            availabilityIndicatorColor = color(67, 168, 67); //green
        } else {
            availabilityIndicatorColor = color(212, 44, 60); //"red";
        }
        fill(availabilityIndicatorColor);

        noStroke();
        rect(
            allLeftPadding,
            availabilityIndicatorY,
            availablilityIndicatorWidth,
            avilabilityIndicatorHeight
        );
        // draw the action buttons
        let actionButtonTopPadding = 10;
        let actionButtonLeftRightPadding = 10;

        let actionButtonX =
            allLeftPadding + availablilityIndicatorWidth + actionButtonLeftRightPadding;
        let actionButtonsTotalWith = this.width - actionButtonX;
        let numOfActionButtons = 3;
        let actionButtonSingleWidth =
            (actionButtonsTotalWith - numOfActionButtons * actionButtonLeftRightPadding) /
            numOfActionButtons;

        let bottomOfAvailabilityIndicator = availabilityIndicatorY + avilabilityIndicatorHeight;

        let actionButtonHeight = avilabilityIndicatorHeight;
        actionButtonHeight = GetMaxHeightByAspectRatio(
            actionButtonSingleWidth,
            actionButtonHeight,
            16 / 9
        );
        let actionButtonsY = bottomOfAvailabilityIndicator - actionButtonHeight;

        this._actionButtons.forEach(btn => {
            let index = this._actionButtons.indexOf(btn);
            btn.Draw(
                actionButtonX + index * (actionButtonSingleWidth + actionButtonLeftRightPadding),
                actionButtonsY,
                actionButtonSingleWidth,
                actionButtonHeight
            );
        });

        // draw the room name
        let roomNameLeftPadding = 10;
        fill("black");
        let minRoomNameTextSize = 12;
        let roomNameTextSize = this.height * 0.035;
        if (roomNameTextSize < minRoomNameTextSize) {
            roomNameTextSize = minRoomNameTextSize;
        }
        textSize(roomNameTextSize);
        textAlign(LEFT, TOP);
        let roomNameX = allLeftPadding + availablilityIndicatorWidth + roomNameLeftPadding;
        let roomNameY = availabilityIndicatorY;
        console.log("roomNameX=", roomNameX);
        noStroke();
        text("<roomName>", roomNameX, availabilityIndicatorY);

        // determine the text size for all labels

        let meetingSubjectTextSize = roomNameTextSize * 2;
        let minMeetingSubjectTextSize = 16;
        if (meetingSubjectTextSize < minMeetingSubjectTextSize) {
            meetingSubjectTextSize = minMeetingSubjectTextSize;
        }

        let minOrganizerTextSize = 14;
        let organizerTextSize = this.height * 0.035;
        if (organizerTextSize < minOrganizerTextSize) {
            organizerTextSize = minOrganizerTextSize;
        }

        let reservationTimeTextSize = this.height * 0.035;
        let minReservationTimeTextSize = 14;
        if (reservationTimeTextSize < minReservationTimeTextSize) {
            reservationTimeTextSize = minReservationTimeTextSize;
        }

        // everything betweeen the room name and action buttons should be spaced evenly
        let interLabelSpacing = avilabilityIndicatorHeight - actionButtonHeight - 20;
        interLabelSpacing -= roomNameTextSize;
        interLabelSpacing -= meetingSubjectTextSize;
        interLabelSpacing -= organizerTextSize;
        interLabelSpacing -= reservationTimeTextSize;
        interLabelSpacing = interLabelSpacing / 3;

        // draw the meeting subject
        let meetingSubjectY = roomNameY + roomNameTextSize + interLabelSpacing;
        textSize(meetingSubjectTextSize);
        text("<meetingSubject>", roomNameX, meetingSubjectY);

        // draw meeting organizer
        let organizerY = meetingSubjectY + meetingSubjectTextSize + interLabelSpacing;
        textSize(organizerTextSize);
        text("<organizer>", roomNameX, organizerY);

        // draw the reservation time
        let reservationTimeY = organizerY + organizerTextSize + interLabelSpacing;
        textSize(reservationTimeTextSize);
        text("<reservationTime>", roomNameX, reservationTimeY);
    }

    GetUpcomingMeetings() {
        let jsonString = fakeData; // for development just using fake data
        let j = JSON.parse(jsonString);
        j.forEach(event => {
            this.AddEvent(event);
        });
    }
}

class TimeLine {
    constructor(x, y, width, height) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
    }
    Draw() {
        noStroke();
        fill("grey");
        rect(this.x, this.y, this.width, this.height);
    }
}

class TimeLineButton {
    constructor() {}
}

let fakeData = `
[
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMVAv05",
    "Duration": 3600.0,
    "End": "2019-10-09T12:30:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI10xLoMkAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQnAAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-09T11:30:00",
    "Subject": "Lunch"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO73",
    "Duration": 1800.0,
    "End": "2019-10-09T13:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI10xLoMkAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsAAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-09T13:00:00",
    "Subject": "Standing UX meeting "
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7y",
    "Duration": 3600.0,
    "End": "2019-10-09T14:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI10xLoMkAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsQAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-09T13:30:00",
    "Subject": "TLPS Collab/Stand up"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7s",
    "Duration": 1800.0,
    "End": "2019-10-09T16:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI10xLoMkAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtuwAAEA==",
    "OrganizerName": "Tom Horon",
    "Start": "2019-10-09T16:00:00",
    "Subject": "PELICAN BAY: Lobby Display - Project Meeting"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYbPl6",
    "Duration": 300.0,
    "End": "2019-10-09T17:05:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI10xLoMkAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQzwAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-09T17:00:00",
    "Subject": "GO HOME"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMVAv05",
    "Duration": 3600.0,
    "End": "2019-10-10T12:30:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI100UyzLAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQnAAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-10T11:30:00",
    "Subject": "Lunch"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7l",
    "Duration": 1800.0,
    "End": "2019-10-10T13:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI100UyzLAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtyQAAEA==",
    "OrganizerName": "Matt Wirsig",
    "Start": "2019-10-10T12:30:00",
    "Subject": "FW: Room Scheduling - PD/PM catch up"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO73",
    "Duration": 1800.0,
    "End": "2019-10-10T13:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI100UyzLAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsAAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-10T13:00:00",
    "Subject": "Standing UX meeting "
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO71",
    "Duration": 1800.0,
    "End": "2019-10-10T13:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI100UyzLAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsgAAEA==",
    "OrganizerName": "Tom Horon",
    "Start": "2019-10-10T13:00:00",
    "Subject": "FW: SAN QUENTIN VI: Room Scheduling System - Project Meeting"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7y",
    "Duration": 3600.0,
    "End": "2019-10-10T14:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI100UyzLAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsQAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-10T13:30:00",
    "Subject": "TLPS Collab/Stand up"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYbPl6",
    "Duration": 300.0,
    "End": "2019-10-10T17:05:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI100UyzLAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQzwAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-10T17:00:00",
    "Subject": "GO HOME"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMQZ0Yy",
    "Duration": 86400.0,
    "End": "2019-10-12T03:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI103d9ZyAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAHloGPb5xQEu/48rCN7NL+ACdvaYEMgAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-11T03:00:00",
    "Subject": "PAY DAY"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMXjp1j",
    "Duration": 3600.0,
    "End": "2019-10-11T12:30:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI103d9ZyAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQoAAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-11T11:30:00",
    "Subject": "Lunch"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7p",
    "Duration": 3600.0,
    "End": "2019-10-11T13:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI103d9ZyAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtwQAAEA==",
    "OrganizerName": "Tim Wood",
    "Start": "2019-10-11T12:00:00",
    "Subject": "Staff Meeting"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7y",
    "Duration": 3600.0,
    "End": "2019-10-11T14:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI103d9ZyAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsQAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-11T13:30:00",
    "Subject": "TLPS Collab/Stand up"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7v",
    "Duration": 3600.0,
    "End": "2019-10-11T17:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI103d9ZyAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtswAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-11T16:00:00",
    "Subject": "Pelican Bay weekly review "
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYbPl6",
    "Duration": 300.0,
    "End": "2019-10-11T17:05:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI103d9ZyAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQzwAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-11T17:00:00",
    "Subject": "GO HOME"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMXjptJ",
    "Duration": 86400.0,
    "End": "2019-10-13T00:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQBGAAAAAAAlV3FfZvuWS4G0Ngplked/BwDH6imC4of+QY0K3wQH6l6QAJ3UpDxVAADraoxmA1JxQ6DHO0PpGQVrAE7omhIAAAA=",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-12T00:00:00",
    "Subject": "Extron Picnic"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7c",
    "Duration": 86400.0,
    "End": "2019-10-15T03:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQBGAAAAAAAlV3FfZvuWS4G0Ngplked/BwDH6imC4of+QY0K3wQH6l6QAJ3UpDxVAADraoxmA1JxQ6DHO0PpGQVrAArcN5BhAAA=",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-14T03:00:00",
    "Subject": "Columbus Day"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7j",
    "Duration": 2700.0,
    "End": "2019-10-14T11:45:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11A5dNnAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxt0AAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-14T11:00:00",
    "Subject": "Standing UX meeting "
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMVAv05",
    "Duration": 3600.0,
    "End": "2019-10-14T12:30:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11A5dNnAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQnAAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-14T11:30:00",
    "Subject": "Lunch"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7y",
    "Duration": 3600.0,
    "End": "2019-10-14T14:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11A5dNnAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsQAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-14T13:30:00",
    "Subject": "TLPS Collab/Stand up"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYbPl6",
    "Duration": 300.0,
    "End": "2019-10-14T17:05:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11A5dNnAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQzwAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-14T17:00:00",
    "Subject": "GO HOME"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMXjp1j",
    "Duration": 3600.0,
    "End": "2019-10-15T12:30:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11ECn0OAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQoAAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-15T11:30:00",
    "Subject": "Lunch"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO73",
    "Duration": 1800.0,
    "End": "2019-10-15T13:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11ECn0OAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsAAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-15T13:00:00",
    "Subject": "Standing UX meeting "
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYXO7y",
    "Duration": 3600.0,
    "End": "2019-10-15T14:30:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11ECn0OAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAAQ2/HyIDiIUmm9Gf5hUZXcgAA1zxtsQAAEA==",
    "OrganizerName": "Sajeeni Nugawila",
    "Start": "2019-10-15T13:30:00",
    "Subject": "TLPS Collab/Stand up"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYbPl6",
    "Duration": 300.0,
    "End": "2019-10-15T17:05:00",
    "HasAttachments": true,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11ECn0OAAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawBO6JoQzwAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-15T17:00:00",
    "Subject": "GO HOME"
  },
  {
    "ChangeKey": "DwAAABYAAABDb8fIgOIhSab0Z/mFRldyAAMYbPl5",
    "Duration": 86400.0,
    "End": "2019-10-17T03:00:00",
    "HasAttachments": false,
    "ItemId": "AAMkADkzMzBkZDQ5LTBlYjYtNDM1Yy05MjgwLTA0OTU0MDJiMTU1ZQFRAAgI11HLya1AAEYAAAAAJVdxX2b7lkuBtDYKZZHnfwcAx+opguKH/kGNCt8EB+pekACd1KQ8VQAA62qMZgNScUOgxztD6RkFawAK3DeQAgAAEA==",
    "OrganizerName": "Grant Miller",
    "Start": "2019-10-16T03:00:00",
    "Subject": "Boss's Day"
  }
]`;
