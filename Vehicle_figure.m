% Experiment parameter settings
v = 1; % Vehicle speed
Time = 1800; % Total time
lambda_max = 1; % Density of RSU (Poisson distribution parameter)
r = 7; % Service circle radius
max_distance = 7; % Maximum distance for Poisson distribution
ts = 5; % Minimum communicable time slot
Time_steps1 = 20; % Time step for vehicle turning monitoring point
Time_steps2 = 7; % Time step interval for scattering RSUs according to Poisson distribution
Time_steps3 = 1; % Time step interval for updating vehicle position
turn_probability = 0.8; % Turn probability, this parameter needs to be modified for different types of vehicles

% Initialization
total_positions = Time / (2 * Time_steps3);
vehicle_positions = zeros(total_positions, 2); % Store vehicle positions
rsu_positions = []; % Store RSU positions
rsu_ids = []; % Store RSU IDs
current_rsu_id = 1; % Starting RSU ID
turn_log = []; % Record turn information

% Expectation value of Poisson distribution lambda_max
lambda = lambda_max;

% Simulate vehicle movement path and generate RSU distribution
vehicle_position = [0, 0]; % Initial position

% Initial direction (to the right)
direction = [1, 0];

% Initialize plot
figure;
hold on;

for t = 1:Time_steps3:Time/2
    index = t / Time_steps3;
    vehicle_positions(index, :) = vehicle_position;
    
    % Plot vehicle position
    plot(vehicle_position(1), vehicle_position(2), 'bo', 'MarkerSize', 1);

    if mod(t, Time_steps1) == 0
        % Determine whether to turn at the turning monitoring point
        turn = rand();
        if turn < turn_probability
            % Turn left or right, equal probability for left and right turns
            angle = pi/2 * (2*randi(2)-3); % pi/2 or -pi/2
            rotation_matrix = [cos(angle), -sin(angle); sin(angle), cos(angle)];
            direction = (rotation_matrix * direction')';
            
            % Record successful turn
            turn_log = [turn_log; t, true];
        else
            % Record failed turn
            turn_log = [turn_log; t, false];
        end
    end
    
    vehicle_position = vehicle_position + v * direction;

    if mod(t, Time_steps2)
        % Generate RSU in the vertical direction at the current vehicle position
        for k = 1:max_distance
            % Calculate the probability of Poisson distribution at position k
            probability = poisspdf(k, lambda);

            % Independently determine whether to generate RSU on the left
            if rand() < probability
                rsu_left = vehicle_position + k * [-direction(2), direction(1)];
                scatter(rsu_left(1), rsu_left(2), 'r.', 'SizeData', 1); % Red dots represent RSU
                rsu_positions = [rsu_positions; rsu_left];
                rsu_ids = [rsu_ids; current_rsu_id];
                current_rsu_id = current_rsu_id + 1;
            end

            % Independently determine whether to generate RSU on the right
            if rand() < probability
                rsu_right = vehicle_position + k * [direction(2), -direction(1)];
                scatter(rsu_right(1), rsu_right(2), 'r.', 'SizeData', 1); % Red dots represent RSU
                rsu_positions = [rsu_positions; rsu_right];
                rsu_ids = [rsu_ids; current_rsu_id];
                current_rsu_id = current_rsu_id + 1;
            end
        end
    end
end

% Plot the road
plot(vehicle_positions(:, 1), vehicle_positions(:, 2), 'b-', 'LineWidth', 1); % Black line represents the road

% Second run, calculate the number of available RSUs
rsu_count = zeros(total_positions, 1);
active_rsus = [];

for t = 1:total_positions
    vehicle_position = vehicle_positions(t, :);
    new_active_rsus = [];
    for i = 1:size(rsu_positions, 1)
        distance = norm(vehicle_position - rsu_positions(i, :));
        if distance <= r
            new_active_rsus = [new_active_rsus; rsu_ids(i)];
        end
    end
    
    % Update the connection time of active RSUs
    new_active_rsus_count = size(new_active_rsus, 1);
    active_rsus_updated = zeros(size(active_rsus));
    active_rsus_index = 1;
    for i = 1:size(active_rsus, 1)
        rsu_id = active_rsus(i, 1);
        idx = find(new_active_rsus == rsu_id, 1);
        if ~isempty(idx)
            active_rsus_updated(active_rsus_index, :) = [rsu_id, active_rsus(i, 2) + 1];
            active_rsus_index = active_rsus_index + 1;
            new_active_rsus(idx) = [];
        end
    end
    active_rsus_updated = active_rsus_updated(1:active_rsus_index - 1, :);

    % Add new active RSUs
    if ~isempty(new_active_rsus)
        for i = 1:min(new_active_rsus_count, size(new_active_rsus, 1))
            rsu_id = new_active_rsus(i);
            active_rsus_updated = [active_rsus_updated; rsu_id, 1];
        end
    end
    
    active_rsus = active_rsus_updated;

    % Count the number of RSUs that meet the conditions
    if ~isempty(active_rsus)
        rsu_count(t) = sum(active_rsus(:, 2) >= ts);
    end
end

% Calculate the average number of available RSUs
average_rsu_count = mean(rsu_count);

% Output results to txt file
fileID = fopen('rsu_count_results.txt', 'w');
fprintf(fileID, 'Number of RSUs meeting the requirements at each position and turning situation:\n');
turn_log_index = 1;
for t = 1:total_positions
    fprintf(fileID, 'Position %d: %d', t, rsu_count(t));
    
    % Determine if it is a monitoring point
    if mod(t, Time_steps1) == 0
        if turn_log(turn_log_index, 2)
            fprintf(fileID, ', Turned\n');
        else
            fprintf(fileID, ', Not turned\n');
        end
        turn_log_index = turn_log_index + 1;
    else
        fprintf(fileID, '\n');
    end
end

fprintf(fileID, '\nAverage number of RSUs: %.2f\n', average_rsu_count);
fclose(fileID);

% Output the average value to the console
fprintf('The average number of RSUs in the communication range of the truck while maintaining normal communication in the Internet of Vehicles is: %.2f\n', average_rsu_count);

% Set legend
legend('Vehicle', 'RSU', 'Location', 'best');
xlabel('X Position');
ylabel('Y Position');
title('Vehicle Movement and RSU Distribution');
hold off;